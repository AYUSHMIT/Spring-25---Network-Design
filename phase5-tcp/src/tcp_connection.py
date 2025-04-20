from tcp_segment import TCPSegment
from rtt_estimator import RTTEstimator
from congestion_control import CongestionControl
import time

class SimpleTCPConnection:
    def __init__(self):
        self.state = 'CLOSED'
        self.send_buffer = bytearray()
        self.receive_buffer = bytearray()
        self.remote_address = None
        self.seq_num = 0
        self.send_base = 0
        self.ack_num = 0
        self.rto = 1.0
        self.window_size = 1024
        self.unacked_segments = {}
        self.rtt_estimator = RTTEstimator()
        self.sent_timestamps = {}
        self.cwnd = 1024
        self.peer_rwnd = 1024
        self.rwnd = 1024
        self.congestion_control = CongestionControl()
        self.expected_seq_num = 0
        self.out_of_order_buffer = {}
        self.max_receive_buffer_size = 4096
        self.retransmitted_segments = set()

    def connect(self, address):
        """Initiates a connection by sending a SYN packet."""
        self.remote_address = address
        self.state = 'SYN_SENT'
        self.seq_num = 0
        self._send_segment(syn=True)
        print(f"Sent SYN to {address}, state: {self.state}")

    def listen(self):
        """Sets the connection to LISTEN state to accept incoming connections."""
        self.state = 'LISTEN'
        print("Listening for incoming connections...")

    def send(self, data):
        """Sends data if the connection is established."""
        if self.state == 'ESTABLISHED':
            self.send_buffer.extend(data)
            while len(self.send_buffer) > 0:
                effective_window = self._send_window()
                if effective_window == 0:
                    print("Effective window is 0, waiting to send...")
                    break
                chunk = self.send_buffer[:min(self.window_size, effective_window)]
                self.send_buffer = self.send_buffer[len(chunk):]
                self._send_segment(data=chunk)
                print(f"Sent data: {chunk}")
        else:
            print("Cannot send data, connection not established.")

    def receive(self, max_bytes):
        """Reads data from the receive buffer for the application."""
        data_to_return = self.receive_buffer[:max_bytes]
        self.receive_buffer = self.receive_buffer[max_bytes:]
        return data_to_return

    def close(self):
        """Initiates the closing sequence by sending a FIN packet."""
        if self.state == 'ESTABLISHED':
            self.state = 'FIN_WAIT_1'
            self._send_segment(fin=True)
            print(f"Sent FIN, state: {self.state}")
        else:
            print("Cannot close, connection not established.")

    def handle_segment(self, segment_bytes, pseudo_header=b''):
        """Handles incoming TCP segments and manages state transitions."""
        try:
            segment = TCPSegment.unpack(segment_bytes, pseudo_header)
            print(f"Received segment: seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}, data={segment.data}")

            if self.state == 'SYN_SENT' and (segment.flags & 0x12) == 0x12:  # SYN-ACK
                self.state = 'ESTABLISHED'
                self.ack_num = segment.seq_num + 1
                self._send_segment(ack=True)
                print("Received SYN-ACK, sent ACK, connection established.")
            elif self.state == 'LISTEN' and (segment.flags & 0x02):  # SYN
                self.state = 'SYN_RCVD'
                self.ack_num = segment.seq_num + 1
                self._send_segment(syn=True, ack=True)
                print("Received SYN, sent SYN-ACK, waiting for ACK.")
            elif self.state == 'SYN_RCVD' and (segment.flags & 0x10):  # ACK
                self.state = 'ESTABLISHED'
                print("Received ACK, connection established.")
            elif self.state == 'FIN_WAIT_1' and (segment.flags & 0x10):  # ACK for FIN
                self.state = 'CLOSED'
                print("Received ACK for FIN, connection closed.")
            elif segment.flags & 0x01:  # FIN
                self.state = 'CLOSE_WAIT'
                self._send_segment(ack=True)
                print("Received FIN, sent ACK, waiting to close.")
            elif segment.flags & 0x10:  # ACK
                self._handle_ack(segment.ack_num, peer_rwnd=segment.rwnd)
            if segment.data:
                self._handle_data(segment)
        except ValueError as e:
            print(f"Error processing segment: {e}")

    def _send_segment(self, syn=False, ack=False, fin=False, data=None, is_retransmission=False, seq_to_retransmit=None):
        """Sends a TCP segment."""
        flags = 0
        if syn:
            flags |= 0x02
        if ack:
            flags |= 0x10
        if fin:
            flags |= 0x01

        seq_num = seq_to_retransmit if is_retransmission else self.seq_num
        segment = TCPSegment(
            seq_num=seq_num,
            ack_num=self.expected_seq_num,
            data=data or b'',
            flags=flags,
            rwnd=self._calculate_rwnd()
        )
        packed_segment = segment.pack()
        self.sent_timestamps[seq_num] = time.time()
        if not is_retransmission:
            self.seq_num += len(data or b'')


    def _handle_ack(self, ack_num, peer_rwnd=None):
        """Handles incoming acknowledgments."""
        if ack_num > self.send_base:
            # Check if the segment was retransmitted
            seq_acked = ack_num - 1  # ACK acknowledges up to ack_num - 1
            was_retransmitted = seq_acked in self.retransmitted_segments

            # Update RTT if the segment was not retransmitted
            if seq_acked in self.sent_timestamps and not was_retransmitted:
                send_time = self.sent_timestamps.pop(seq_acked)
                sample_rtt = time.time() - send_time
                if sample_rtt >= 0:  # Ensure RTT is valid
                    print(f"DEBUG _handle_ack: Calling rtt_estimator.update with sample_rtt={sample_rtt:.4f}")
                    self.rtt_estimator.update(sample_rtt)
            elif was_retransmitted:
                # Remove timestamp even if not used for RTT calculation
                self.sent_timestamps.pop(seq_acked, None)
                print(f"Ignoring RTT sample for retransmitted segment ACK {ack_num}")

            # Update send_base and peer_rwnd
            self.send_base = ack_num
            if peer_rwnd is not None:
                self.peer_rwnd = peer_rwnd

            # Notify congestion control about the new acknowledgment
            print("DEBUG _handle_ack: Calling congestion_control.on_ack_received")
            self.congestion_control.on_ack_received(is_new_ack=True)

            # Remove acknowledged segments from unacked_segments
            for seq in list(self.unacked_segments.keys()):
                if seq < ack_num:
                    del self.unacked_segments[seq]

    def _retransmit_segment(self, seq_num):
        """Retransmits the segment with the given sequence number."""
        if seq_num in self.unacked_segments:
            segment = self.unacked_segments[seq_num]
            print(f"Retransmitting segment with seq {seq_num}")
            # Update timestamp for retransmission
            self.sent_timestamps[seq_num] = time.time()
            # Retransmit the segment
            self._send_segment(is_retransmission=True, seq_to_retransmit=seq_num)


    def _handle_data(self, segment):
        """Processes incoming data segments, handles order and duplicates."""
        seq_num = segment.seq_num
        data = segment.data
        data_len = len(data)

        if seq_num < self.expected_seq_num:
            # Duplicate data for already acknowledged segment, just ACK again
            print(f"Received duplicate segment: seq={seq_num}, expected={self.expected_seq_num}")
            self._send_ack_segment()
            return

        if seq_num == self.expected_seq_num:
            # In-order segment
            print(f"Received in-order segment: seq={seq_num}")
            # Check if buffer has space
            if len(self.receive_buffer) + data_len <= self.max_receive_buffer_size:
                self.receive_buffer.extend(data)
                self.expected_seq_num += data_len

                # Check if buffered segments can now be added
                while self.expected_seq_num in self.out_of_order_buffer:
                    buffered_data = self.out_of_order_buffer.pop(self.expected_seq_num)
                    if len(self.receive_buffer) + len(buffered_data) <= self.max_receive_buffer_size:
                        self.receive_buffer.extend(buffered_data)
                        self.expected_seq_num += len(buffered_data)
                    else:
                        # Buffer full, put it back (or handle differently)
                        self.out_of_order_buffer[self.expected_seq_num - len(buffered_data)] = buffered_data
                        break  # Stop processing buffered data for now

                self._send_ack_segment()  # Send ACK for the contiguous block received
            else:
                # Buffer overflow, drop segment and rely on sender timeout/retransmit
                print("Receive buffer overflow, dropping in-order segment.")
                # Consider sending ACK for previously received data if not done recently

        elif seq_num > self.expected_seq_num:
            # Out-of-order segment
            print(f"Received out-of-order segment: seq={seq_num}, expected={self.expected_seq_num}")
            # Buffer it if space available and not already buffered
            if seq_num not in self.out_of_order_buffer and \
            (self._calculate_buffered_size() + data_len) <= self.max_receive_buffer_size:
                self.out_of_order_buffer[seq_num] = data
                print(f"Buffered out-of-order segment {seq_num}")
            else:
                print(f"Dropping out-of-order segment {seq_num} (duplicate or buffer full)")
            # Send duplicate ACK for the last in-order sequence number received
            self._send_ack_segment()  # ACK indicates expected_seq_num


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
        segment = TCPSegment(
            seq_num=self.seq_num,  # Sender's sequence number (usually static for pure ACKs)
            ack_num=self.expected_seq_num,  # Acknowledging up to this received sequence number
            data=b'',
            flags=0x10  # ACK flag
        )
        segment.rwnd = current_rwnd  # Set the receiver window size in the segment
        packed_segment = segment.pack()  # Assuming TCPSegment.pack handles the rwnd field
        print(f"Sending ACK for seq {self.expected_seq_num} with rwnd={current_rwnd}")
        # Simulate sending the packed_segment via UDP socket
        # self._send_raw_segment(packed_segment)  # Example send call
    def _send_window(self):
        """Calculates the effective send window size."""
        return min(self.cwnd, self.peer_rwnd)




    def _check_timers(self):
        """Checks for retransmission timeouts and retransmits if necessary."""
        current_time = time.time()
        # Get dynamic RTO, fall back to default if None or invalid
        rto_val = self.rtt_estimator.get_timeout()
        check_rto = rto_val if rto_val is not None and rto_val > 0 else self.rto

        print(f"DEBUG _check_timers: Using RTO = {check_rto}")  # Debug print

        for seq, timestamp in list(self.sent_timestamps.items()):
            # Use the determined RTO value for comparison
            if current_time - timestamp > check_rto:
                print(f"Timeout for segment {seq}, retransmitting... (elapsed={current_time - timestamp:.4f} > RTO={check_rto})")
                # Notify congestion control about the timeout
                print("DEBUG _check_timers: Calling congestion_control.on_timeout")
                self.congestion_control.on_timeout()

                # Retransmit the segment
                self._retransmit_segment(seq)

                # Break after handling the first timeout (TCP typically handles one timeout at a time)
                break

    def _trigger_fast_retransmit(self):
        """Triggers fast retransmission on duplicate ACKs."""
        print("Fast retransmit triggered.")
        # Logic to retransmit the segment