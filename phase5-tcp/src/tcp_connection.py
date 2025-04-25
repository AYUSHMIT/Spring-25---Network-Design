from tcp_segment import TCPSegment
from rtt_estimator import RTTEstimator
from congestion_control import CongestionControl
import time
import threading
class SimpleTCPConnection:
    def __init__(self):
        self.state = 'CLOSED'
        self.send_buffer = bytearray()
        self.receive_buffer = bytearray()
        self.seq_num = 0
        self.send_base = 0
        self.ack_num = 0
        self.rto = 1.0
        self.window_size = 1024 # This might be related to rwnd or initial cwnd, clarify its use
        self.unacked_segments = {} # To store segments that have been sent but not yet acknowledged
        self.rtt_estimator = RTTEstimator()
        self.sent_timestamps = {} # To store timestamps of sent segments for RTT calculation
        self.cwnd = 1 # Start with cwnd = 1 in Slow Start
        self.ssthresh = 64 # Initial ssthresh
        self.peer_rwnd = 1024 # Assume initial peer receiver window
        self.rwnd = 4096 # Initial receiver window size (max receive buffer size)
        self.congestion_control = CongestionControl()
        self.expected_seq_num = 0 # Next sequence number expected by the receiver
        self.out_of_order_buffer = {} # To buffer out-of-order segments
        self.max_receive_buffer_size = 4096 # Maximum size of the receive buffer
        self.retransmitted_segments = set() # To track retransmitted segments for Karn's Algorithm
        self.mss = 1024  # Maximum Segment Size (initialized)

        # Logs for plotting
        self.cwnd_log = []
        self.rtt_log = []
        self.rto_log = []
        self.transfer_complete = False
        self.total_data_sent = 0 # Track total application data sent AND ACKED
        self.total_data_to_send = 0 # Track total application data to send

        # Attributes for socket, simulator, and remote address
        self.sock = None
        self.simulator = None
        self.remote_address = None

        # Timer for retransmissions (needs to be managed by a separate mechanism, e.g., a thread)
        self._retransmission_timer = None
        self._timer_thread = None # To manage timers in a separate thread

        self._start_timer_thread() # Start the timer thread

    def _start_timer_thread(self):
        """Starts a separate thread to check timers periodically."""
        if self._timer_thread is None or not self._timer_thread.is_alive():
            self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self._timer_thread.start()
            print("DEBUG: Timer thread started.")


    def _timer_loop(self):
        """Timer loop to periodically check for retransmission timeouts."""
        while True:
            if self.state != 'CLOSED': # Only check timers if connection is active
                 self._check_timers()
            time.sleep(0.1) # Check timers every 100ms (adjust as needed)


    def is_transfer_complete(self):
        """Check if the transfer is complete."""
        # The transfer is complete when all original data has been sent and acknowledged.
        # This means send_base should be equal to the total amount of data sent from the application.
        print(f"DEBUG: Checking transfer completion: send_base={self.send_base}, seq_num={self.seq_num}, total_data_sent={self.total_data_sent}, total_data_to_send={self.total_data_to_send}, send_buffer={len(self.send_buffer)}, unacked_segments={len(self.unacked_segments)}")
        # Check if all application data has been sent AND all sent data has been acknowledged
        return self.send_base >= self.total_data_to_send and not self.send_buffer and not self.unacked_segments

    def connect(self, address):
        """Initiates a connection by sending a SYN packet."""
        self.remote_address = address
        self.state = 'SYN_SENT'
        self.seq_num = 0 # Initial sequence number
        # SYN consumes one sequence number
        syn_segment = TCPSegment(seq_num=self.seq_num, ack_num=0, data=b'', flags=0x02)
        self._send_segment(syn_segment) # Send SYN with initial seq num
        self.seq_num += 1 # Increment seq_num after sending SYN
        print(f"Sent SYN to {address}, state: {self.state}")
        # Start a timer for the SYN packet (managed by _check_timers and unacked_segments)


    def send(self, data):
        """Send application data."""
        print("DEBUG: send() method in tcp_connection.py is being executed.")
        print("DEBUG: Client attempting to send data.")
        # Assuming 'data' here is the initial bulk data from the application
        # Accumulate total data to send if multiple send calls are made
        self.total_data_to_send = len(data) # If only one send call for the whole file

        self.send_buffer.extend(data)  # Append new data to the send buffer
        print(f"DEBUG: Appended {len(data)} bytes to send buffer. Total in buffer: {len(self.send_buffer)}")


        if self.state == 'ESTABLISHED':
            print("DEBUG: Connection established, attempting to send from buffer from send().")
            self._send_from_buffer() # Attempt to send buffered data if established


    def _send_from_buffer(self):
        """Send segments from the send buffer if the connection is established and window allows."""
        if self.state != 'ESTABLISHED' and self.state != 'CLOSE_WAIT': # Allow sending FIN in CLOSE_WAIT
            print(f"DEBUG: Connection state {self.state}. Cannot send data segments from buffer.")
            return

        # Calculate effective send window size: min(cwnd, peer_rwnd) - unacked_data
        unacked_bytes = self.seq_num - self.send_base
        effective_window = min(self.cwnd, self.peer_rwnd)
        sendable_bytes = effective_window - unacked_bytes
        print(f"DEBUG: Effective window size: {effective_window}, Unacked bytes: {unacked_bytes}, Sendable bytes: {sendable_bytes}")
        print(f"DEBUG: Data in send buffer: {len(self.send_buffer)}")


        # Send data from the buffer while respecting the effective window
        # and ensuring we don't exceed the amount of data available in the send buffer.
        while self.send_buffer and sendable_bytes > 0:
            # Calculate chunk size, limited by MSS, sendable_bytes, and available data in buffer
            chunk_size = min(self.mss, len(self.send_buffer), sendable_bytes)
            if chunk_size <= 0:
                 print("DEBUG: Chunk size is 0 or less, breaking send from buffer loop.")
                 break # No more data can be sent within the window or buffer is empty

            # Get a chunk of data from the beginning of the send buffer
            chunk = self.send_buffer[:chunk_size]

            # Create and send the data segment
            # The sequence number for this segment is the current self.seq_num
            segment = TCPSegment(
                 seq_num=self.seq_num,
                 ack_num=self.expected_seq_num, # Acknowledge received data
                 data=chunk,
                 flags=0, # Data segment has no special flags
                 rwnd=self._calculate_rwnd() # Include receiver window
            )
            # Store the segment being sent in unacked_segments and its timestamp
            # This is done in _send_segment

            self._send_segment(segment) # Send the data segment

            # Increment sequence number for the next byte to be sent
            self.seq_num += chunk_size
            sendable_bytes -= chunk_size # Decrease sendable bytes from the window
            print(f"DEBUG: Sent chunk of size {chunk_size}, new seq_num={self.seq_num}, remaining sendable_bytes={sendable_bytes}")

            # Do NOT remove data from send_buffer here. Data is removed in _handle_ack when acknowledged.


    def close(self):
        """Initiates the closing sequence by sending a FIN packet."""
        # Ensure all data is sent and acknowledged before sending FIN (simplification: check send_buffer and unacked_segments)
        if self.state == 'ESTABLISHED' and not self.send_buffer and not self.unacked_segments:
            self.state = 'FIN_WAIT_1'
            # FIN consumes one sequence number
            fin_segment = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=0x01)
            self._send_segment(fin_segment)
            self.seq_num += 1 # Increment seq_num after sending FIN
            print(f"Sent FIN, state: {self.state}")
            # Start a timer for the FIN packet (managed by _check_timers and unacked_segments)
        elif self.state != 'ESTABLISHED':
             print("Cannot close, connection not established.")
        else:
             print("DEBUG: Data transfer not complete, cannot send FIN yet.")


    def handle_segment(self, segment_bytes, pseudo_header=b'', client_address=None):
        """Handles incoming TCP segments and manages state transitions."""
        try:
            segment = TCPSegment.unpack(segment_bytes, pseudo_header)
            print(f"DEBUG: Received segment: seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}, data={segment.data}")

            # State transitions based on received flags
            # Server side
            if self.state == 'LISTEN' and (segment.flags & 0x02):  # SYN received by server
                print("DEBUG: Server received SYN")
                if client_address:
                    self.remote_address = client_address  # Set the client address
                else:
                    print("ERROR: Client address is None, cannot respond with SYN-ACK.")
                    return
                self.state = 'SYN_RCVD'
                self.expected_seq_num = segment.seq_num + 1  # Server expects next byte after client's SYN
                # Send SYN-ACK. SYN consumes one sequence number on server side.
                self.seq_num = 0  # Server's initial sequence number
                syn_ack_segment = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=0x12)
                self._send_segment(syn_ack_segment)
                self.seq_num += 1  # Increment server's seq_num for SYN-ACK
                print("DEBUG: Server sent SYN-ACK")

            elif self.state == 'SYN_RCVD' and (segment.flags & 0x10):  # ACK received by server (completing handshake)
                print("DEBUG: Server received ACK, connection established")
                # Verify ACK number here (should be server's SYN_ACK seq + 1)
                if segment.ack_num == self.seq_num:  # Check if ACK acknowledges our SYN-ACK
                    self.state = 'ESTABLISHED'
                    # Server is ready to receive data now.
                    print("DEBUG: Server connection established.")

            # Client side
            elif self.state == 'SYN_SENT' and (segment.flags & 0x12) == 0x12:  # SYN-ACK received by client
                print("DEBUG: Client received SYN-ACK")
                # Verify sequence number of SYN-ACK (should be server's initial seq num)
                # Verify ACK number (should be client's initial SYN seq + 1)
                if segment.ack_num == self.seq_num:  # Check if SYN-ACK acknowledges our SYN
                    self.expected_seq_num = segment.seq_num + 1  # Client expects next byte after server's SYN
                    self.ack_num = self.expected_seq_num  # Client's ack number
                    self.state = 'ESTABLISHED'
                    # Send final ACK. Pure ACK does not consume sequence number.
                    ack_segment = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=0x10)
                    self._send_segment(ack_segment)
                    print("DEBUG: Client sent ACK, connection established")

                    # Start sending buffered data after handshake completion
                    if self.send_buffer:
                        print("DEBUG: Sending buffered data after handshake.")
                        self._send_from_buffer()  # Trigger sending from buffer

            # Both client and server
            elif segment.flags & 0x01:  # FIN received
                print("DEBUG: Received FIN")
                # If in ESTABLISHED state, transition to CLOSE_WAIT
                if self.state == 'ESTABLISHED':
                    self.state = 'CLOSE_WAIT'
                    self.expected_seq_num = segment.seq_num + 1  # Acknowledge FIN
                    ack_segment = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=0x10)
                    self._send_segment(ack_segment)
                    print("DEBUG: Sent ACK for FIN, state: CLOSE_WAIT")
                elif self.state == 'FIN_WAIT_2':  # Received FIN in FIN_WAIT_2 (simultaneous close)
                    self.expected_seq_num = segment.seq_num + 1  # Acknowledge FIN
                    ack_segment = TCPSegment(seq_num=self.seq_num, ack_num=self.expected_seq_num, data=b'', flags=0x10)
                    self._send_segment(ack_segment)
                    self.state = 'TIME_WAIT'
                    print("DEBUG: Received FIN in FIN_WAIT_2, sent ACK, state: TIME_WAIT")
                    # Start 2*MSL timer (not implemented here)

            elif segment.flags & 0x10:  # ACK received
                print(f"DEBUG: Received ACK for seq={segment.ack_num}")
                self._handle_ack(segment.ack_num, peer_rwnd=segment.rwnd)
                # After processing ACK, attempt to send more data if any is buffered and window allows
                if self.state == 'ESTABLISHED' and self.send_buffer:
                    self._send_from_buffer()
                # Handle ACK for our FIN segment (in FIN_WAIT_1 state)
                elif self.state == 'FIN_WAIT_1' and segment.ack_num == self.seq_num:
                    self.state = 'FIN_WAIT_2'
                    print("DEBUG: Received ACK for our FIN, state: FIN_WAIT_2")

            # Handle data if present in the segment and connection is established
            if segment.data and (self.state == 'ESTABLISHED' or self.state == 'FIN_WAIT_2'):  # Allow receiving data in FIN_WAIT_2
                self._handle_data(segment)

        except ValueError as e:
            print(f"DEBUG: Error processing segment: {e}")
            # Handle checksum errors or other segment unpacking issues (e.g., send RST)
    # Modify _send_segment to accept a TCPSegment object
    def _send_segment(self, segment: TCPSegment, is_retransmission=False):
        """Sends a TCP segment."""
        print(f"DEBUG: Preparing to send segment: seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}, data={segment.data}")

        # Pseudo-header requires source IP, dest IP, protocol (6 for TCP), and TCP length.
        # You'll need to add source and dest IP attributes to SimpleTCPConnection
        # and pass them here to form the pseudo-header for correct checksum calculation.
        # For now, packing without pseudo-header might work in a simple local simulation,
        # but it's not standard TCP checksum calculation.
        packed_segment = segment.pack() # Assuming pack handles checksum without pseudo-header for now


        # Store sent segment and timestamp for retransmission (only for segments that consume seq numbers: SYN, FIN, Data)
        # Pure ACKs do not consume sequence numbers and are generally not retransmitted based on a timer,
        # but rather sent as duplicate ACKs upon receiving out-of-order segments.
        if segment.data or (segment.flags & 0x02) or (segment.flags & 0x01):
             self.unacked_segments[segment.seq_num] = segment # Store the segment object
             self.sent_timestamps[segment.seq_num] = time.time() # Store timestamp
             print(f"DEBUG: Stored segment {segment.seq_num} in unacked_segments.")


        try:
            if self.simulator:
                self.simulator.sendto(self.sock, packed_segment, self.remote_address)
            else:
                self.sock.sendto(packed_segment, self.remote_address)
            print(f"DEBUG: Sent segment to {self.remote_address} with seq={segment.seq_num}, flags={segment.flags}")
        except Exception as e:
            print(f"Socket send error in _send_segment for seq={segment.seq_num}, flags={segment.flags}: {e}")
            import traceback
            traceback.print_exc() # Add full traceback


    def _handle_ack(self, ack_num, peer_rwnd=None):
        """Handles incoming ACK segments."""
        print(f"DEBUG _handle_ack: Received ACK num: {ack_num}, current send_base: {self.send_base}")
        # An ACK confirms receipt of data up to ack_num - 1.
        # We need to check if this ACK acknowledges new data.
        if ack_num > self.send_base:
            newly_acked_bytes = ack_num - self.send_base

            # Remove acknowledged segments from unacked_segments and calculate RTT
            # Iterate through unacked segments to find those fully acknowledged by this ACK
            # Need to be careful here, ACK could acknowledge multiple segments.
            # Remove segments with sequence numbers less than ack_num.
            acked_seq_nums = [seq for seq in self.unacked_segments if seq < ack_num]
            for acked_seq in sorted(acked_seq_nums):
                 # Only update RTT for the first time a segment is acknowledged (Karn's Algorithm)
                 # Need a way to track if a segment is a retransmission for RTT calculation.
                 # Your current _retransmit_segment adds to retransmitted_segments, use this.
                 if acked_seq in self.sent_timestamps and acked_seq not in self.retransmitted_segments: # Check for Karn's
                    sample_rtt = time.time() - self.sent_timestamps.pop(acked_seq)
                    self.rtt_estimator.update(sample_rtt)
                    self.rtt_log.append((time.time(), sample_rtt))
                    print(f"DEBUG _handle_ack: Updated RTT with sample: {sample_rtt:.4f}")
                 elif acked_seq in self.sent_timestamps:
                      # If it was a retransmission, remove timestamp but don't update RTT
                      self.sent_timestamps.pop(acked_seq)
                      print(f"DEBUG _handle_ack: Ignoring RTT for retransmitted segment {acked_seq}")

                 # Remove from unacked_segments
                 self.unacked_segments.pop(acked_seq, None)
                 print(f"DEBUG _handle_ack: Removed segment {acked_seq} from unacked_segments.")


            self.send_base = ack_num # Update send_base to the highest byte acknowledged + 1
            # total_data_sent should potentially track acknowledged application data bytes
            # If self.send_base directly tracks acknowledged application data bytes, this might be correct.
            # Ensure your seq_num for data segments correctly represents byte stream offsets.
            # Assuming send_base advancing means these bytes are sent and acknowledged.
            # The logic here depends on how seq_num is managed for data.
            # If seq_num increments by data length, send_base tracks acknowledged bytes.
            # self.total_data_sent = self.send_base # If send_base correctly tracks acknowledged bytes

            print(f"DEBUG _handle_ack: Updated send_base to {self.send_base}")

            # Update peer receiver window if provided
            if peer_rwnd is not None:
                self.peer_rwnd = peer_rwnd
                print(f"DEBUG _handle_ack: Updated peer_rwnd to {self.peer_rwnd}")

            # Congestion control: Increase cwnd if in Slow Start or Congestion Avoidance
            # Need to pass whether it's a new ACK or duplicate ACK to congestion control.
            # This _handle_ack structure needs to differentiate new ACKs from duplicate ACKs for CC.
            # A new ACK advances send_base.
            self.congestion_control.on_ack_received(is_new_ack=True) # Assuming new ACK if send_base advanced
            self.cwnd = self.congestion_control.get_congestion_window()
            self.cwnd_log.append((time.time(), self.cwnd))
            print(f"DEBUG _handle_ack: Updated cwnd to {self.cwnd}")


        else:
            # This is a duplicate ACK if ack_num == send_base
            print(f"DEBUG _handle_ack: Received duplicate ACK for ack={ack_num}")
            # Congestion control: Handle duplicate ACKs
            # Only call on_duplicate_ack if the ACK number is the same as send_base (duplicate ACK)
            if ack_num == self.send_base:
                fast_retransmit_needed = self.congestion_control.on_duplicate_ack()
                self.cwnd = self.congestion_control.get_congestion_window()
                self.cwnd_log.append((time.time(), self.cwnd))
                print(f"DEBUG _handle_ack: Duplicate ACK, updated cwnd to {self.cwnd}")
                if fast_retransmit_needed:
                     print("DEBUG _handle_ack: Triggering fast retransmit.")
                     # Trigger fast retransmit (send the segment at send_base)
                     self._retransmit_segment(self.send_base) # Retransmit the segment at send_base
            else:
                 # ACK is less than send_base - very old duplicate or out of order ACK, ignore for CC
                 print(f"DEBUG _handle_ack: Received old or out-of-order ACK for ack={ack_num}, ignoring for CC.")


        # After processing ACK, attempt to send more data if any is buffered and window allows
        if self.state == 'ESTABLISHED' and self.send_buffer:
            self._send_from_buffer()



    def _retransmit_segment(self, seq_num):
        """Retransmits the segment with the given sequence number."""
        # Find the segment in unacked_segments
        # The sequence number to retransmit should be the base of the window (send_base) for TCP Reno/Tahoe on triple duplicate ACK.
        # If a timeout occurs, retransmit the segment that timed out.
        # Your current _retransmit_segment takes seq_num as argument, which works for both.

        segment_to_retransmit = self.unacked_segments.get(seq_num)

        if segment_to_retransmit:
            print(f"Retransmitting segment with seq {seq_num}")
            # Mark this segment as retransmitted to prevent RTT calculation (Karn's Algorithm)
            self.retransmitted_segments.add(seq_num)
            # Update timestamp for retransmission (use current time for RTO calculation for this retransmission timer)
            self.sent_timestamps[seq_num] = time.time()

            # Retransmit the segment object
            self._send_segment(segment_to_retransmit, is_retransmission=True)

        else:
             print(f"DEBUG _retransmit_segment: Segment with seq {seq_num} not found in unacked_segments. Cannot retransmit.")


    def _handle_data(self, segment):
        """Processes incoming data segments, handles order and duplicates."""
        seq_num = segment.seq_num
        data = segment.data
        data_len = len(data)

        # Ignore data if connection is not in a state to receive data
        if self.state != 'ESTABLISHED' and self.state != 'FIN_WAIT_2': # Allow receiving data in FIN_WAIT_2
             print(f"DEBUG _handle_data: Received data segment with seq={seq_num} in state {self.state}, ignoring.")
             # Consider sending a RST if receiving data in an unexpected state

        # If receive buffer is full, drop segment and rely on sender timeout/retransmit
        if len(self.receive_buffer) + self._calculate_buffered_size() + data_len > self.max_receive_buffer_size:
             print(f"DEBUG _handle_data: Receive buffer overflow for segment seq={seq_num}, dropping.")
             # Send an ACK for the last in-order byte received to signal receive window
             self._send_ack_segment() # Send ACK with current rwnd
             return


        if seq_num < self.expected_seq_num:
            # Duplicate data for already acknowledged segment, just ACK again
            print(f"Received duplicate segment: seq={seq_num}, expected={self.expected_seq_num}")
            self._send_ack_segment() # Send duplicate ACK
            return

        if seq_num == self.expected_seq_num:
            # In-order segment
            print(f"Received in-order segment: seq={seq_num}, expected={self.expected_seq_num}")
            self.receive_buffer.extend(data)
            self.expected_seq_num += data_len

            # Check if buffered segments can now be added
            # Process any buffered segments that are now in order
            while self.expected_seq_num in self.out_of_order_buffer:
                print(f"DEBUG _handle_data: Processing buffered segment with seq={self.expected_seq_num}")
                buffered_data = self.out_of_order_buffer.pop(self.expected_seq_num)
                buffered_data_len = len(buffered_data)
                self.receive_buffer.extend(buffered_data)
                self.expected_seq_num += buffered_data_len
                print(f"DEBUG _handle_data: Added buffered segment to receive buffer. New expected_seq_num={self.expected_seq_num}")


            self._send_ack_segment()  # Send cumulative ACK for the contiguous block received

        elif seq_num > self.expected_seq_num:
            # Out-of-order segment
            print(f"Received out-of-order segment: seq={seq_num}, expected={self.expected_seq_num}")
            # Buffer it if not already buffered
            if seq_num not in self.out_of_order_buffer:
                self.out_of_order_buffer[seq_num] = data
                print(f"Buffered out-of-order segment {seq_num}")
            else:
                print(f"Dropping duplicate out-of-order segment {seq_num}")

            # Always send duplicate ACK for the last in-order sequence number received when receiving out-of-order data
            self._send_ack_segment() # ACK indicates expected_seq_num

        # After handling data, check if transfer is complete from receiver's perspective
        # This might involve checking if all expected data has been received and processed.
        # The completion check in simulation_runner is sender-side, but receiver also needs to know when to close.


    def _calculate_buffered_size(self):
        """Calculates the total size of data in the out-of-order buffer."""
        return sum(len(data) for data in self.out_of_order_buffer.values())

    def _calculate_rwnd(self):
        """Calculates the current available receiver window size."""
        # Consider both main buffer and out-of-order buffer occupancy
        occupied_buffer = len(self.receive_buffer) + self._calculate_buffered_size()
        available_space = self.max_receive_buffer_size - occupied_buffer
        return max(0, available_space)  # Ensure rwnd is not negative




    def _send_ack_segment(self):
        """Sends an ACK segment with the current receiver window size."""
        current_rwnd = self._calculate_rwnd()
        # The sequence number for pure ACKs is typically the last sent sequence number.
        # For simplicity here, we can use the current self.seq_num which represents the sequence number
        # for the next byte the sender will send. A pure ACK does not consume a sequence number.
        segment = TCPSegment(
            seq_num=self.seq_num,  # Sender's current sequence number (doesn't increment for pure ACK)
            ack_num=self.expected_seq_num,  # Acknowledging up to this received sequence number
            data=b'',
            flags=0x10,  # ACK flag
            rwnd=current_rwnd # Set the receiver window size
        )
        # Checksum calculation should include pseudo-header (add source/dest IPs to class)
        packed_segment = segment.pack()

        # Send the packed_segment via UDP socket (using simulator if available)
        try:
            if self.simulator:
                self.simulator.sendto(self.sock, packed_segment, self.remote_address)
            else:
                self.sock.sendto(packed_segment, self.remote_address)
            print(f"DEBUG: Sent ACK segment to {self.remote_address} with ack={self.expected_seq_num}, rwnd={current_rwnd}")
        except Exception as e:
            print(f"Socket send error in _send_ack_segment: {e}")
            import traceback
            traceback.print_exc() # Add full traceback


    def _send_window(self):
        """Calculates the effective send window size."""
        return min(self.cwnd, self.peer_rwnd)




    def _check_timers(self):
        """Checks for retransmission timeouts and retransmits if necessary."""
        current_time = time.time()
        # Get dynamic RTO, fall back to default if None or invalid
        rto_val = self.rtt_estimator.get_timeout()
        # Ensure RTO is at least a minimum value (e.g., 1 second) and not negative
        check_rto = max(1.0, rto_val) if rto_val is not None and rto_val > 0 else 1.0


        # Check timers only if there are unacknowledged segments that are eligible for timeout
        # Exclude pure ACKs which are not in unacked_segments with timestamps in this logic.
        # Only consider segments with sequence numbers less than the current seq_num (data/SYN/FIN)
        unacked_timed_segments = {seq: ts for seq, ts in self.sent_timestamps.items() if seq < self.seq_num}


        if unacked_timed_segments:
            # Find the segment with the smallest sequence number among those with timers
            oldest_seq_with_timer = min(unacked_timed_segments.keys())
            oldest_timestamp = unacked_timed_segments[oldest_seq_with_timer]


            if (current_time - oldest_timestamp) > check_rto:
                print(f"Timeout for segment {oldest_seq_with_timer}, retransmitting... (elapsed={current_time - oldest_timestamp:.4f} > RTO={check_rto:.4f})")
                self.rto_log.append((time.time(), check_rto)) # Log the RTO that caused timeout

                # Notify congestion control about the timeout
                print("DEBUG _check_timers: Calling congestion_control.on_timeout")
                self.congestion_control.on_timeout()
                self.cwnd = self.congestion_control.get_congestion_window()
                self.cwnd_log.append((time.time(), self.cwnd))
                print(f"DEBUG _check_timers: After timeout, cwnd = {self.cwnd}")

                # Retransmit the segment that timed out
                self._retransmit_segment(oldest_seq_with_timer)

                # After a timeout and retransmission, restart the timer for the retransmitted segment.
                # The timestamp is updated in _retransmit_segment.
                # For TCP Tahoe/Reno, after timeout, cwnd is reset to 1 and ssthresh updated.

                # In a simple RDT, you might only have one timer for the oldest unacked segment.
                # If you have a timer for each segment, you'd iterate through all and retransmit
                # segments whose timers have expired. TCP typically has a single retransmission timer
                # for the oldest unacked segment. Your current loop iterates all but breaks after the first.

        # If no unacked timed segments, log the current RTO based on the estimator
        elif rto_val is not None:
            self.rto_log.append((time.time(), check_rto)) # Log current RTO even if no timeout


    # No separate _trigger_fast_retransmit method needed here, it's handled within _handle_ack
    # when triple duplicate ACKs are detected and congestion_control.on_duplicate_ack returns True.
    # The _handle_ack method calls _retransmit_segment directly in that case.