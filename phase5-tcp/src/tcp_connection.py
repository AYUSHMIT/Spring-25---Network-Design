import socket
import time
import threading
import traceback # Import traceback for detailed error logging

from tcp_segment import TCPSegment
from rtt_estimator import RTTEstimator
from congestion_control import CongestionControl

class SimpleTCPConnection:
    def __init__(self):
        self.state = 'CLOSED'
        self.send_buffer = bytearray()
        self.receive_buffer = bytearray()
        self.seq_num = 0
        self.send_base = 0
        self.ack_num = 0
        self.rto = 1.0
        self.unacked_segments = {}
        self.rtt_estimator = RTTEstimator()
        self.sent_timestamps = {}
        self.peer_rwnd = 1024
        self.rwnd = 4096
        self.congestion_control = CongestionControl()
        self.expected_seq_num = 0
        self.out_of_order_buffer = {}
        self.max_receive_buffer_size = 4096
        self.retransmitted_segments = set()
        self.mss = 1024
        self.cwnd_log = []
        self.rtt_log = []
        self.rto_log = []
        self.total_data_to_send = 0
        self.sock = None
        self.simulator = None
        self.remote_address = None
        self.lock = threading.Lock()
        self._timer_thread = None
        self._start_timer_thread()

    def _send_segment(self, segment: TCPSegment, is_retransmission=False):
        """Packs and sends a TCP segment using the simulator or socket."""
        print(f"DEBUG _send_segment: Preparing: seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}, data_len={len(segment.data)}, retransmit={is_retransmission}")

        try:
            packed_segment = segment.pack()
        except Exception as e:
            print(f"ERROR: Failed to pack segment seq={segment.seq_num}: {e}")
            return

        consumes_seq = segment.data or (segment.flags & 0x02) or (segment.flags & 0x01)
        if consumes_seq:
            with self.lock:
                if not is_retransmission:
                    self.unacked_segments[segment.seq_num] = segment
                    self.sent_timestamps[segment.seq_num] = time.time()
                    print(f"DEBUG _send_segment: Stored segment {segment.seq_num} in unacked_segments.")
                else:
                    if segment.seq_num in self.sent_timestamps:
                        self.sent_timestamps[segment.seq_num] = time.time()
                        print(f"DEBUG _send_segment: Updated timestamp for retransmitted segment {segment.seq_num}.")

        try:
            dest_addr = self.remote_address
            if not dest_addr:
                print(f"ERROR _send_segment: No remote address set for seq={segment.seq_num}")
                return

            if self.simulator:
                self.simulator.sendto(self.sock, packed_segment, dest_addr)
            else:
                self.sock.sendto(packed_segment, dest_addr)
            print(f"DEBUG _send_segment: Sent to {dest_addr} - seq={segment.seq_num}, flags={segment.flags}")
        except Exception as e:
            print(f"ERROR _send_segment: Socket send error for seq={segment.seq_num}, flags={segment.flags}: {e}")
            traceback.print_exc()








    def _start_timer_thread(self):
        """Starts a separate thread to check timers periodically."""
        if self._timer_thread is None or not self._timer_thread.is_alive():
            self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self._timer_thread.start()
            print("DEBUG: Timer thread started.")

    def _calculate_rwnd_locked(self):
        """Calculates the available receive window size. Assumes lock is held."""
        max_receive_buffer_size = 4096
        occupied = len(self.receive_buffer) + sum(len(data) for data in self.out_of_order_buffer.values())
        available = max_receive_buffer_size - occupied
        return max(0, available)




    def _timer_loop(self):
        """Timer thread for handling retransmissions."""
        while self.state != 'CLOSED':  # Exit when the connection is closed
            self._check_timers()
            time.sleep(0.1)  # Check timers every 100ms

    def is_transfer_complete(self):
        """Check if the transfer is complete."""
        with self.lock: # Lock needed to read shared state consistently
            # Assumes data sequence numbers start after SYN (e.g., at 1)
            all_data_acked = self.send_base >= (self.total_data_to_send + 1)
            buffer_empty = not self.send_buffer
            no_unacked_segments = not self.unacked_segments
            # Completion also requires that no timers are pending/active
            no_pending_timers = not self.sent_timestamps

            print(f"DEBUG: Checking transfer completion: send_base={self.send_base}, total_data_to_send={self.total_data_to_send}, all_data_acked={all_data_acked}, buffer_empty={buffer_empty}, no_unacked={no_unacked_segments}, no_timers={no_pending_timers}")
            # All conditions must be met
            return all_data_acked and buffer_empty and no_unacked_segments and no_pending_timers

    def connect(self, address):
        """Initiates a connection by sending a SYN packet."""
        segment_to_send = None
        with self.lock: # Lock needed to modify shared state
            if self.state != 'CLOSED':
                print("WARN: Connect called on non-closed connection.")
                return
            self.remote_address = address
            self.state = 'SYN_SENT'
            self.seq_num = 0 # Start with ISN = 0
            self.send_base = 0 # Base hasn't moved yet
            self.expected_seq_num = 0 # Haven't received anything yet
            # Prepare SYN segment
            syn_segment = TCPSegment(
                seq_num=self.seq_num,
                ack_num=0,
                data=b'',
                flags=0x02, # SYN flag
                rwnd=self._calculate_rwnd_locked() # Include our rwnd (lock already held)
            )
            segment_to_send = syn_segment
            # SYN consumes one sequence number conceptually
            # We increment seq_num *after* sending, but before releasing lock
            self.seq_num += 1
            print(f"Sent SYN to {address}, state: {self.state}, next seq: {self.seq_num}")

        # Send segment outside lock
        if segment_to_send:
            self._send_segment(segment_to_send)

    def send(self, data):
        """Appends data to the send buffer and tries to send it."""
        if not data:
            return

        print("DEBUG: send() method called.")
        should_try_sending = False
        with self.lock: # Lock needed to modify shared buffer and counters
            if self.total_data_to_send == 0: # Assume one call to send() with all data
                 self.total_data_to_send = len(data)
                 print(f"DEBUG: Total data to send set to {self.total_data_to_send}")

            self.send_buffer.extend(data)
            print(f"DEBUG: Appended {len(data)} bytes to send buffer. Total in buffer: {len(self.send_buffer)}")

            # Check if we can send immediately
            if self.state == 'ESTABLISHED':
                 should_try_sending = True

        if should_try_sending:
            print("DEBUG: Connection established, attempting to send from buffer via send().")
            self._send_from_buffer() # Try sending (handles locking internally)

    def _send_from_buffer(self):
        """Send segments from the send buffer based on available window."""
        print("DEBUG _send_from_buffer: Attempting to send.")
        while True: # Loop to send multiple segments if window allows
            segment_to_send = None
            chunk_size_sent = 0
            next_seq_num_after_send = 0

            with self.lock: # Acquire lock to read state and prepare segment
                current_state = self.state
                if current_state != 'ESTABLISHED' and current_state != 'CLOSE_WAIT':
                    if current_state != 'CLOSED': # Avoid logging if intentionally closed
                        print(f"DEBUG _send_from_buffer: Connection state {current_state}. Cannot send.")
                    break # Exit loop and function

                current_cwnd = self.congestion_control.get_congestion_window()
                peer_window = self.peer_rwnd
                window_size = min(current_cwnd, peer_window)
                current_seq_num = self.seq_num
                current_send_base = self.send_base
                buffer_len = len(self.send_buffer)

                # Calculate how much data is in flight
                in_flight = current_seq_num - current_send_base
                # Calculate how many *new* bytes we are allowed to send
                sendable_bytes = int(window_size - in_flight)

                # Determine starting index in buffer for unsent data
                buffer_start_index = current_seq_num - current_send_base
                available_in_buffer = buffer_len - buffer_start_index

                print(f"DEBUG _send_from_buffer: state={current_state}, cwnd={current_cwnd:.2f}, peer_rwnd={peer_window}, eff_wnd={window_size}, seq={current_seq_num}, base={current_send_base}, inflight={in_flight}, sendable={sendable_bytes}, buf_avail={available_in_buffer}")

                # Check conditions to stop sending
                if sendable_bytes <= 0 or available_in_buffer <= 0:
                    if sendable_bytes <= 0: print("DEBUG _send_from_buffer: Window is full or closed.")
                    if available_in_buffer <= 0:
                        if buffer_len == 0 : print("DEBUG _send_from_buffer: Send buffer is empty.")
                        else: print(f"WARN _send_from_buffer: No data available at index {buffer_start_index} (seq={current_seq_num}, base={current_send_base}). Buffer len={buffer_len}")
                    break # Exit loop

                # Determine chunk size
                chunk_size = min(self.mss, sendable_bytes, available_in_buffer)
                if chunk_size <= 0:
                    print(f"DEBUG _send_from_buffer: Calculated chunk_size={chunk_size}. Breaking.")
                    break

                # Get the chunk
                buffer_end_index = buffer_start_index + chunk_size
                chunk = self.send_buffer[buffer_start_index:buffer_end_index]
                print(f"DEBUG _send_from_buffer: Selected chunk index {buffer_start_index}:{buffer_end_index}")

                # Prepare segment
                segment_to_send = TCPSegment(
                     seq_num=current_seq_num,
                     ack_num=self.expected_seq_num, # ACK peer's data
                     data=bytes(chunk),
                     flags=0,
                     rwnd=self._calculate_rwnd_locked() # Our receive window
                )
                # --- Update state *immediately* after deciding to send ---
                self.seq_num += chunk_size
                chunk_size_sent = chunk_size # Store size for logging
                next_seq_num_after_send = self.seq_num # Store new seq num for logging
                # ----------------------------------------------------------

            # --- Release lock before sending ---
            if segment_to_send:
                 print(f"DEBUG _send_from_buffer: Sending chunk size={chunk_size_sent}, next seq_num will be {next_seq_num_after_send}")
                 self._send_segment(segment_to_send) # Send segment (handles its own locking for storing)
                 # Loop continues automatically to check if more can be sent
            else:
                break # Exit loop if no segment was prepared (e.g., window full)

    def close(self):
        """Initiates the closing sequence by sending a FIN packet."""
        fin_segment_to_send = None
        next_seq_num = 0
        with self.lock: # Needs lock to read/write state and check resources
            buffer_empty = not self.send_buffer
            no_unacked = not self.unacked_segments
            is_established = self.state == 'ESTABLISHED'
            current_seq = self.seq_num

            print(f"DEBUG close(): state={self.state}, buffer_empty={buffer_empty}, no_unacked={no_unacked}")

            if is_established and buffer_empty and no_unacked:
                self.state = 'FIN_WAIT_1'
                fin_segment_to_send = TCPSegment(
                    seq_num=current_seq,
                    ack_num=self.expected_seq_num,
                    data=b'',
                    flags=0x01, # FIN flag
                    rwnd=self._calculate_rwnd_locked()
                )
                self.seq_num += 1 # FIN consumes one sequence number
                next_seq_num = self.seq_num
                print(f"DEBUG close(): State -> FIN_WAIT_1, prepared FIN seq={fin_segment_to_send.seq_num}, next seq={next_seq_num}")
            # Handle other states if needed (e.g., CLOSE_WAIT -> LAST_ACK)
            elif self.state == 'CLOSE_WAIT':
                 # Application indicated close after receiving peer's FIN
                 self.state = 'LAST_ACK'
                 fin_segment_to_send = TCPSegment(
                    seq_num=current_seq,
                    ack_num=self.expected_seq_num,
                    data=b'',
                    flags=0x01, # FIN flag
                    rwnd=self._calculate_rwnd_locked()
                 )
                 self.seq_num += 1
                 next_seq_num = self.seq_num
                 print(f"DEBUG close(): State -> LAST_ACK, prepared FIN seq={fin_segment_to_send.seq_num}, next seq={next_seq_num}")
            elif not is_established and self.state != 'CLOSE_WAIT':
                 print(f"WARN: Close called in invalid state: {self.state}")
            else: # Established but buffer/unacked not empty
                 print(f"DEBUG close(): Cannot send FIN yet. State={self.state}, Buffer Empty={buffer_empty}, Unacked Empty={no_unacked}")

        # Send FIN outside the lock
        if fin_segment_to_send:
             self._send_segment(fin_segment_to_send)
             print(f"Sent FIN, state changed.")

    def handle_segment(self, segment_bytes, pseudo_header=b'', client_address=None):
        """Handles incoming TCP segments, unpacks, and directs to state handlers."""
        try:
            # Unpack the segment
            segment = TCPSegment.unpack(segment_bytes, pseudo_header)
            print(f"DEBUG handle_segment: Received segment: seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}, data_len={len(segment.data)}")
        except ValueError as e:
            print(f"DEBUG handle_segment: Checksum error or unpack failed: {e}")
            return  # Discard segment

        segment_to_send = None
        next_state = None
        trigger_send_buffer = False
        processed = False  # Flag to track if segment was handled

        with self.lock:  # Lock for state checks and modifications
            current_state = self.state

            # --- State Machine Logic ---

            # Server: LISTEN state expects SYN
            if current_state == 'LISTEN' and (segment.flags & TCPSegment.SYN):  # SYN
                print("DEBUG handle_segment: Server received SYN")
                if client_address:
                    self.remote_address = client_address
                    next_state = 'SYN_RCVD'
                    self.expected_seq_num = segment.seq_num + 1
                    self.seq_num = 0  # Server's ISN
                    current_rwnd = self._calculate_rwnd_locked()
                    segment_to_send = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=TCPSegment.SYN | TCPSegment.ACK, rwnd=current_rwnd)  # SYN+ACK
                    self.seq_num += 1  # Increment for the SYN
                    print(f"DEBUG handle_segment: Server LISTEN -> SYN_RCVD. Prepared SYN-ACK.")
                    processed = True
                else:
                    print("ERROR handle_segment: Client address missing for SYN.")
                    # Cannot proceed without address

            # Server: SYN_RCVD state expects ACK
            elif current_state == 'SYN_RCVD':
                # Server expecting ACK for its SYN-ACK
                if segment.flags & TCPSegment.ACK:
                    if segment.ack_num == self.seq_num:  # Correct ACK for our SYN-ACK
                        print("DEBUG handle_segment: Server received valid ACK for SYN-ACK. State SYN_RCVD -> ESTABLISHED.")
                        # Update state and clean up SYN-ACK timer
                        self.state = 'ESTABLISHED'
                        self.send_base = segment.ack_num  # Update send_base
                        self.unacked_segments.pop(0, None)  # Assuming SYN-ACK was seq 0
                        self.sent_timestamps.pop(0, None)

                        # Now, immediately check if the current segment has data OR if buffered data can be processed
                        if len(segment.data) > 0 and segment.seq_num == self.expected_seq_num:
                            print(f"DEBUG handle_segment: Processing data piggybacked on final ACK (seq={segment.seq_num}).")
                            self._handle_data_locked(segment)  # Process piggybacked data
                        else:
                            # Process any buffered out-of-order data
                            print(f"DEBUG handle_segment: Checking out-of-order buffer after ACK. Expecting {self.expected_seq_num}")
                            while self.expected_seq_num in self.out_of_order_buffer:
                                buffered_data = self.out_of_order_buffer.pop(self.expected_seq_num)
                                self.receive_buffer.extend(buffered_data)
                                self.expected_seq_num += len(buffered_data)
                                print(f"DEBUG handle_segment: Processed buffered segment. Updated expected_seq_num to {self.expected_seq_num}")

                        self.peer_rwnd = segment.rwnd  # Update peer window
                        processed = True
                    else:
                        print(f"DEBUG handle_segment: Server received ACK in SYN_RCVD, but ack num {segment.ack_num} != expected {self.seq_num}. Ignoring.")
                elif len(segment.data) > 0 and segment.seq_num == self.expected_seq_num:
                    # Data arrived before final ACK. Buffer it.
                    print(f"DEBUG handle_segment: Received data segment (seq={segment.seq_num}) in SYN_RCVD state. Buffering.")
                    if segment.seq_num not in self.out_of_order_buffer:  # Avoid buffering duplicates
                        self.out_of_order_buffer[segment.seq_num] = segment.data
                        print(f"DEBUG handle_segment: Buffered segment seq={segment.seq_num}.")
                    processed = True  # Mark as processed (buffered)
                else:
                    # Handle other flags if necessary (e.g., client resends SYN?)
                    print(f"WARN handle_segment: Unexpected segment (seq={segment.seq_num}, flags={segment.flags}) received in SYN_RCVD. Ignoring.")

            # Client: SYN_SENT state expects SYN-ACK
            elif current_state == 'SYN_SENT' and (segment.flags & (TCPSegment.SYN | TCPSegment.ACK)) == (TCPSegment.SYN | TCPSegment.ACK):  # SYN-ACK
                print("DEBUG handle_segment: Client received SYN-ACK")
                if segment.ack_num == self.seq_num:  # Check if it ACKs our SYN
                    print("DEBUG handle_segment: Client SYN acknowledged by SYN-ACK.")
                    self.send_base = segment.ack_num  # Our SYN (seq=0) is acked, base becomes 1
                    print(f"DEBUG handle_segment: Client send_base updated to {self.send_base}")
                    # Remove original SYN from tracking
                    original_syn_seq = self.send_base - 1
                    if original_syn_seq in self.unacked_segments:
                        self.unacked_segments.pop(original_syn_seq)
                        print(f"DEBUG handle_segment: Removed SYN {original_syn_seq} from unacked.")
                    if original_syn_seq in self.sent_timestamps:
                        self.sent_timestamps.pop(original_syn_seq)
                        print(f"DEBUG handle_segment: Removed SYN {original_syn_seq} timestamp.")

                    next_state = 'ESTABLISHED'
                    self.expected_seq_num = segment.seq_num + 1  # Expect byte after server's SYN
                    self.peer_rwnd = segment.rwnd  # Update peer window from SYN-ACK
                    print(f"DEBUG handle_segment: Client updated peer_rwnd to {self.peer_rwnd}")
                    # Prepare final ACK
                    client_rwnd = self._calculate_rwnd_locked()
                    segment_to_send = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=TCPSegment.ACK, rwnd=client_rwnd)  # ACK
                    print(f"DEBUG handle_segment: Client SYN_SENT -> ESTABLISHED. Prepared final ACK.")
                    if self.send_buffer:
                        trigger_send_buffer = True  # Signal to send data after ACK
                    processed = True
                else:
                    print(f"DEBUG handle_segment: Client received SYN-ACK but ack num {segment.ack_num} != expected {self.seq_num}. Ignoring.")

            # Server: ESTABLISHED state processes data and ACKs
            elif current_state == 'ESTABLISHED':
                ack_to_send = None  # Variable to hold potential ACK
                if len(segment.data) > 0:  # Segment contains data
                    print(f"DEBUG handle_segment: Processing data segment in ESTABLISHED state (seq={segment.seq_num}).")
                    ack_to_send = self._handle_data_locked(segment)  # Capture the ACK segment
                    processed = True
                elif segment.flags & TCPSegment.ACK:  # Segment contains an ACK
                    print(f"DEBUG handle_segment: Processing ACK in ESTABLISHED state (ack={segment.ack_num}).")
                    ack_processed, can_send_more = self._handle_ack_locked(segment.ack_num, segment.rwnd)
                    processed = ack_processed
                    if can_send_more:
                        trigger_send_buffer = True

                # Assign the ACK segment to be sent
                if ack_to_send:
                    segment_to_send = ack_to_send

            # --- Update State Safely ---
            if next_state and next_state != current_state:
                print(f"DEBUG handle_segment: Updating state from {self.state} to {next_state}")
                self.state = next_state
            elif next_state and next_state == current_state:
                print(f"DEBUG handle_segment: State remains {current_state}")

        # --- Release lock before sending ---
        if segment_to_send:
            self._send_segment(segment_to_send)  # Handles its own lock for storing if needed
        if trigger_send_buffer:
            print("DEBUG handle_segment: Triggering send from buffer.")
            with self.lock:
                current_state_for_send = self.state
            if current_state_for_send == 'ESTABLISHED':
                self._send_from_buffer()

        if not processed:
            with self.lock:
                final_state = self.state
            if final_state not in ['CLOSED', 'TIME_WAIT']:
                print(f"WARN handle_segment: Segment (seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}) not processed in state {current_state} -> {final_state}.")



    def _handle_ack_locked(self, ack_num, peer_rwnd):
        """
        Handles ACK processing. Must be called with lock held.
        Returns tuple: (ack_was_processed, can_send_more)
        """
        processed = False
        can_send = False
        current_send_base = self.send_base # Read under lock

        if ack_num > current_send_base: # New ACK
            print(f"DEBUG _handle_ack_locked: New ACK received: ack={ack_num}")
            newly_acked_bytes = ack_num - current_send_base

            # Remove acknowledged data from the send buffer
            if newly_acked_bytes > 0:
                 if len(self.send_buffer) >= newly_acked_bytes:
                     self.send_buffer = self.send_buffer[newly_acked_bytes:]
                     print(f"DEBUG _handle_ack_locked: Removed {newly_acked_bytes} bytes from send_buffer. Remaining: {len(self.send_buffer)}")
                 else:
                     print(f"WARN _handle_ack_locked: Trying to remove {newly_acked_bytes} bytes, but buffer only has {len(self.send_buffer)}. Clearing buffer.")
                     self.send_buffer = bytearray()

            # Remove acknowledged segments from tracking and update RTT
            acked_seq_nums = [seq for seq in self.unacked_segments if seq < ack_num]
            for acked_seq in sorted(acked_seq_nums):
                if acked_seq in self.sent_timestamps: # Check if timestamp exists
                    if acked_seq not in self.retransmitted_segments: # Karn's Algorithm check
                        sample_rtt = time.time() - self.sent_timestamps.pop(acked_seq) # Pop timestamp
                        print(f"DEBUG _handle_ack_locked: RTT sample for {acked_seq}: {sample_rtt:.4f}")
                        self.rtt_estimator.update(sample_rtt)
                        self.rtt_log.append((time.time(), sample_rtt))
                        print(f"DEBUG: rtt_log updated: {self.rtt_log[-1]}")
                    else:
                        # It was retransmitted, just pop timestamp, don't update RTT
                        self.sent_timestamps.pop(acked_seq)
                        self.retransmitted_segments.discard(acked_seq) # Clear retransmit flag
                        print(f"DEBUG _handle_ack_locked: Ignoring RTT for retransmitted segment {acked_seq}")
                # else: # Don't warn if timestamp already gone
                     # print(f"WARN _handle_ack_locked: Timestamp for acknowledged seq {acked_seq} not found.")

                # Remove from unacked segments dictionary
                removed_segment = self.unacked_segments.pop(acked_seq, None)
                if removed_segment:
                     print(f"DEBUG _handle_ack_locked: Removed segment {acked_seq} from unacked_segments.")
                # else: # Don't warn if segment already removed
                    # print(f"WARN _handle_ack_locked: Tried to remove segment {acked_seq} but it wasn't found.")

            # Update send_base
            self.send_base = ack_num
            print(f"DEBUG _handle_ack_locked: Updated send_base to {self.send_base}")

            # Update peer window
            if peer_rwnd is not None: # Check if rwnd was provided
                 self.peer_rwnd = peer_rwnd
                 print(f"DEBUG _handle_ack_locked: Updated peer_rwnd to {self.peer_rwnd}")

            # Congestion control: Increase cwnd
            self.congestion_control.on_ack_received(is_new_ack=True)
            new_cwnd = self.congestion_control.get_congestion_window()
            self.cwnd_log.append((time.time(), new_cwnd))
            print(f"DEBUG: cwnd_log updated: {self.cwnd_log[-1]}")
            print(f"DEBUG _handle_ack_locked: CC: New ACK -> cwnd = {new_cwnd:.2f}")

            processed = True
            can_send = True # New ACK might open window

        elif ack_num == current_send_base: # Duplicate ACK
            print(f"DEBUG _handle_ack_locked: Duplicate ACK received: ack={ack_num}")
            # Update peer window even on duplicate ACK
            if peer_rwnd is not None: self.peer_rwnd = peer_rwnd

            # Congestion control: Handle duplicate ACKs
            fast_retransmit_needed = self.congestion_control.on_duplicate_ack()
            new_cwnd = self.congestion_control.get_congestion_window()
            self.cwnd_log.append((time.time(), new_cwnd)) # Log cwnd changes
            print(f"DEBUG: cwnd_log updated: {self.cwnd_log[-1]}")
            print(f"DEBUG _handle_ack_locked: CC: Dup ACK -> cwnd = {new_cwnd:.2f}")

            processed = True # ACK was processed (as duplicate)
            if fast_retransmit_needed:
                 print("DEBUG _handle_ack_locked: Fast Retransmit Triggered for seq {current_send_base}.")
                 # We need a way to signal the retransmission *after* releasing the lock
                 # For now, just logging. The timer will eventually handle it if needed,
                 # but Fast Retransmit would be faster. Implementation deferred.

        else: # Old ACK (ack_num < send_base)
             print(f"DEBUG _handle_ack_locked: Old ACK received: ack={ack_num}, base={current_send_base}. Ignoring.")
             # Still update peer window if provided
             if peer_rwnd is not None: self.peer_rwnd = peer_rwnd
             processed = True # Processed as "old"

        return processed, can_send



    def _handle_data_locked(self, segment):
        """
        Processes incoming data. Must be called with lock held.
        Returns the ACK segment to send, or None.
        """
        seq_num = segment.seq_num
        data = segment.data
        data_len = len(data)

        # Check against expected sequence number
        current_expected = self.expected_seq_num  # Read under lock

        # --- Buffer Check ---
        occupied_buffer = len(self.receive_buffer) + self._calculate_buffered_size_locked()
        if occupied_buffer + data_len > self.max_receive_buffer_size:
            print(f"DEBUG _handle_data_locked: Receive buffer overflow for seg seq={seq_num}. Dropping.")
            return self._create_ack_segment_locked()  # Resend ACK

        # --- Process Data ---
        if seq_num < current_expected:
            print(f"DEBUG _handle_data_locked: Received duplicate data: seq={seq_num}, expected={current_expected}")
            return self._create_ack_segment_locked()  # Resend ACK

        elif seq_num == current_expected:
            print(f"DEBUG _handle_data_locked: Received in-order segment: seq={seq_num}")
            self.receive_buffer.extend(data)
            self.expected_seq_num += data_len  # Advance expected number

            # Check buffer for contiguous segments
            while self.expected_seq_num in self.out_of_order_buffer:
                print(f"DEBUG _handle_data_locked: Processing buffered segment seq={self.expected_seq_num}")
                buffered_data = self.out_of_order_buffer.pop(self.expected_seq_num)
                self.receive_buffer.extend(buffered_data)
                self.expected_seq_num += len(buffered_data)
                print(f"DEBUG _handle_data_locked: Advanced expected_seq_num to {self.expected_seq_num}")

            # Simulate application layer consuming the data
            print(f"DEBUG _handle_data_locked: Simulating consumption of {len(self.receive_buffer)} bytes.")
            self.receive_buffer.clear()  # Clear the buffer to free up space

            # Send cumulative ACK
            return self._create_ack_segment_locked()

        elif seq_num > current_expected:
            print(f"DEBUG _handle_data_locked: Received out-of-order segment: seq={seq_num}, expected={current_expected}")
            if seq_num not in self.out_of_order_buffer:
                self.out_of_order_buffer[seq_num] = data
                print(f"DEBUG _handle_data_locked: Buffered out-of-order segment {seq_num}")
            else:
                print(f"DEBUG _handle_data_locked: Received duplicate out-of-order segment {seq_num}. Discarding.")
            # Send duplicate ACK for the current expected sequence number
            return self._create_ack_segment_locked()

        return None  # Should not be reached if logic covers all cases





    def _calculate_rwnd(self):
        """Calculates available receive window size. Acquires lock."""
        with self.lock:
            # Option 1: Call the existing _locked helper method
            # return self._calculate_rwnd_locked()

            # Option 2: Perform calculation directly here (more self-contained)
            occupied = len(self.receive_buffer) + self._calculate_buffered_size_locked()
            available = self.max_receive_buffer_size - occupied
            return max(0, available)



    def _calculate_buffered_size_locked(self):
        """Calculates out-of-order buffer size. Assumes lock is held."""
        # Ensure this method is present in your file
        return sum(len(d) for d in self.out_of_order_buffer.values())



    def _create_ack_segment_locked(self):
         """Creates an ACK segment. Assumes lock is held."""
         current_rwnd = self._calculate_rwnd_locked()
         return TCPSegment(
             seq_num=self.seq_num, # Our current next send seq num
             ack_num=self.expected_seq_num, # Acking up to this received seq num
             data=b'',
             flags=0x10, # ACK
             rwnd=current_rwnd
         )








    def _retransmit_segment_external(self, segment):
         """Helper to call _send_segment for retransmission outside the main lock."""
         # Add to retransmitted set for Karn's algorithm *before* sending
         with self.lock: # Lock needed only for this brief update
             self.retransmitted_segments.add(segment.seq_num)
             print(f"DEBUG _retransmit_segment_external: Marked {segment.seq_num} for Karn's algorithm.")
         # Call send_segment (which handles its own lock for timestamp update)
         self._send_segment(segment, is_retransmission=True)

    def _check_timers(self):
        """Checks for retransmission timeouts and cleans up expired timestamps."""
        current_time = time.time()
        rto_val = self.rtt_estimator.get_timeout()
        check_rto = max(1.0, rto_val) if rto_val is not None and rto_val > 0 else 1.0  # Ensure RTO is reasonable

        # Log the current RTO value
        self.rto_log.append((current_time, rto_val))
        print(f"DEBUG: rto_log updated: {self.rto_log[-1]}")



        seq_to_retransmit = None
        timestamps_to_remove = []

        # --- Read shared state under lock ---
        with self.lock:
            current_unacked_keys = set(self.unacked_segments.keys())
            items_to_check = list(self.sent_timestamps.items())
        # --- Lock released ---

        # Find all expired sequence numbers
        expired_seqs = [seq for seq, ts in items_to_check if (current_time - ts) > check_rto]

        if not expired_seqs:  # No timers expired
            return

        # Identify segments needing retransmission vs. just timestamp cleanup
        for seq in expired_seqs:
            if seq in current_unacked_keys:
                seq_to_retransmit = seq  # Candidate for retransmission
            else:
                timestamps_to_remove.append(seq)  # Mark timestamp for removal

        # --- Perform Timestamp Cleanup (lock needed) ---
        if timestamps_to_remove:
            with self.lock:
                for seq in timestamps_to_remove:
                    if seq in self.sent_timestamps:  # Check if still exists
                        print(f"DEBUG _check_timers: Removing expired timestamp for seq={seq}.")
                        self.sent_timestamps.pop(seq, None)

        # --- Prepare for Retransmission if needed ---
        if seq_to_retransmit is not None:
            with self.lock:
                segment = self.unacked_segments.get(seq_to_retransmit)
                if segment:
                    print(f"DEBUG _check_timers: Retransmitting seq={seq_to_retransmit}.")
                    self._retransmit_segment_external(segment)