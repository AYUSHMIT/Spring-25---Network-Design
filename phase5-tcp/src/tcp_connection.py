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
        self.seq_num = 0  # Current sequence number
        self.send_base = 0  # Base of the send window
        self.ack_num = 0  # Next expected acknowledgment number
        self.rto = 1.0  # Default retransmission timeout
        self.window_size = 1024  # Example window size
        self.unacked_segments = {}  # Tracks unacknowledged segments for retransmission
        self.rtt_estimator = RTTEstimator()  # RTT estimator instance
        self.sent_timestamps = {}  # Tracks timestamps of sent segments for RTT calculation
        self.cwnd = 1024  # Congestion window size (example value)
        self.peer_rwnd = 1024  # Peer receive window size (example value)
        self.rwnd = 1024  # Receiver window size (example value)
        self.congestion_control = CongestionControl()  # Congestion control instance

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

    def receive(self):
        """Receives data if the connection is established."""
        if self.state == 'ESTABLISHED':
            print("Receiving data...")
            return self.receive_buffer
        else:
            print("Cannot receive data, connection not established.")
            return None

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
            # Unpack the segment using the TCPSegment class
            segment = TCPSegment.unpack(segment_bytes, pseudo_header)
            print(f"Received segment: seq={segment.seq_num}, ack={segment.ack_num}, flags={segment.flags}, data={segment.data}")

            # Process the segment based on flags and current state
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
                self._handle_data(segment.data)
        except ValueError as e:
            print(f"Error processing segment: {e}")

    def _send_segment(self, syn=False, ack=False, fin=False, data=None):
        """Simulates sending a TCP segment with the specified flags."""
        flags = 0
        if syn:
            flags |= 0x02  # SYN flag
        if ack:
            flags |= 0x10  # ACK flag
        if fin:
            flags |= 0x01  # FIN flag

        segment = TCPSegment(
            seq_num=self.seq_num,
            ack_num=self.ack_num,
            data=data or b'',
            flags=flags
        )
        segment.rwnd = self.rwnd  # Set the receiver window size
        packed_segment = segment.pack()
        self.unacked_segments[self.seq_num] = packed_segment
        self.sent_timestamps[self.seq_num] = time.time()  # Track send time
        self.seq_num += len(data) if data else 1
        print(f"Sending segment: {packed_segment}")

    def _handle_ack(self, ack_num, peer_rwnd=None):
        """Handles incoming acknowledgments and updates the send buffer."""
        if ack_num > self.send_base:
            print(f"ACK received: {ack_num}")
            self.congestion_control.on_ack_received()  # Update congestion control
            sample_rtt = time.time() - self.sent_timestamps.pop(ack_num, time.time())  # Calculate SampleRTT
            self.rtt_estimator.update(sample_rtt)  # Update RTT estimator
            self.send_base = ack_num
            # Update peer receive window if provided
            if peer_rwnd is not None:
                self.peer_rwnd = peer_rwnd
            # Remove acknowledged segments
            for seq in list(self.unacked_segments.keys()):
                if seq < ack_num:
                    del self.unacked_segments[seq]
        else:
            print("Duplicate or out-of-order ACK received.")

    def _handle_data(self, data):
        """Processes incoming data and appends it to the receive buffer."""
        if len(self.receive_buffer) + len(data) > self.rwnd:
            print("Receive buffer overflow, dropping data.")
            return
        self.receive_buffer.extend(data)
        print(f"Data received: {data}")
        self._send_ack_segment()  # Send an ACK with updated rwnd

    def _send_ack_segment(self):
        """Sends an ACK segment with the current receiver window size."""
        segment = TCPSegment(
            seq_num=self.seq_num,
            ack_num=self.ack_num,
            data=b'',
            flags=0x10  # ACK flag
        )
        segment.rwnd = self.rwnd  # Set the receiver window size
        packed_segment = segment.pack()
        print(f"Sending ACK with rwnd={self.rwnd}: {packed_segment}")

    def _send_window(self):
        """Calculates the effective send window size."""
        return min(self.congestion_control.get_congestion_window(), self.peer_rwnd)

    def _check_timers(self):
        """Checks for retransmission timeouts and retransmits if necessary."""
        rto = self.rtt_estimator.get_timeout()  # Get the current RTO
        print(f"Current RTO: {rto}")
        # Logic to check timers and retransmit unacknowledged segments
        # If a timeout occurs:
        self.congestion_control.on_timeout()

    def _trigger_fast_retransmit(self):
        """Triggers fast retransmission on duplicate ACKs."""
        print("Fast retransmit triggered.")
        # Logic to retransmit the segment