import socket
import time
import threading
import json
import traceback
from tcp_segment import TCPSegment
from rtt_estimator import RTTEstimator
from congestion_control import CongestionControl

class SimpleTCPConnection:
    CLOSED = 0
    LISTEN = 1
    SYN_SENT = 2
    SYN_RECEIVED = 3
    ESTABLISHED = 4
    FIN_WAIT_1 = 5
    FIN_WAIT_2 = 6
    CLOSE_WAIT = 7
    CLOSING = 8
    LAST_ACK = 9
    TIME_WAIT = 10

    def __init__(self, sock, addr, network_simulator=None):
        self.sock = sock
        self.remote_address = addr
        self.simulator = network_simulator
        self.state = self.CLOSED

        self.send_buffer = bytearray()
        self.receive_buffer = bytearray()
        self.seq_num = 1
        self.send_base = 0
        self.ack_num = 0
        self.expected_seq_num = 1
        self.mss = 1024
        self.max_receive_buffer_size = 65536

        self.unacked_segments = {}
        self.sent_timestamps = {}
        self.out_of_order_buffer = {}
        self.retransmitted_segments = set()

        self.congestion_control = CongestionControl()
        self.rtt_estimator = RTTEstimator()
        self.peer_rwnd = 65535
        self.rwnd = 65535

        self.rto = 1.0
        self.start_time = time.time()
        self.cwnd_log = []
        self.rtt_log = []
        self.rto_log = []

        self.total_data_to_send = 0

        self.lock = threading.Lock()
        self.is_running = True
        self._timer_thread = None
        self._start_timer_thread()

    def _start_timer_thread(self):
        if self._timer_thread is None or not self._timer_thread.is_alive():
            self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self._timer_thread.start()
            print("DEBUG: Timer thread started.")

    def _timer_loop(self):
        while self.is_running and self.state != self.CLOSED:
            try:
                self._check_timers()
                time.sleep(0.1)
            except Exception as e:
                print(f"CRITICAL ERROR in _timer_loop: {e}")
                traceback.print_exc()
                break

    def log_cwnd(self):
        self.cwnd_log.append({
            "time": time.time() - self.start_time,
            "cwnd": self.congestion_control.get_congestion_window()
        })

    def connect(self, remote_address):
        """Initiate a connection to the remote address."""
        with self.lock:
            self.remote_address = remote_address
            self.state = self.SYN_SENT
            syn_segment = TCPSegment(seq_num=self.seq_num, ack_num=0, flags=TCPSegment.SYN, data=b'')
            self._send_segment(syn_segment)
            print(f"DEBUG: Sent SYN to {remote_address}")

    def send(self, data):
        if not data:
            return

        with self.lock:
            if self.total_data_to_send == 0:
                self.total_data_to_send = len(data)
            self.send_buffer.extend(data)
            self.log_cwnd()

        if self.state == self.ESTABLISHED:
            self._send_from_buffer()

    def _send_from_buffer(self):
        with self.lock:
            if self.state != self.ESTABLISHED:
                return

            current_seq = self.seq_num
            inflight = current_seq - self.send_base
            available_window = int(min(self.congestion_control.get_congestion_window(), self.peer_rwnd) - inflight)

            buffer_start = current_seq - 1
            available_data = len(self.send_buffer) - buffer_start

            while available_window > 0 and available_data > 0:
                chunk_size = min(available_window, available_data, self.mss)
                if chunk_size <= 0:
                    break

                data_chunk = self.send_buffer[buffer_start:buffer_start+chunk_size]
                segment = TCPSegment(
                    seq_num=current_seq,
                    ack_num=self.expected_seq_num,
                    flags=0,
                    rwnd=self._calculate_rwnd_locked(),
                    data=data_chunk
                )
                self._send_segment(segment)

                self.unacked_segments[segment.seq_num] = segment
                self.sent_timestamps[segment.seq_num] = time.time()

                self.seq_num += len(data_chunk)
                current_seq = self.seq_num
                inflight = current_seq - self.send_base
                available_window = int(min(self.congestion_control.get_congestion_window(), self.peer_rwnd) - inflight)
                buffer_start = current_seq - 1
                available_data = len(self.send_buffer) - buffer_start

            if available_window <= 0 or available_data <= 0:
                self.send_buffer = bytearray()  # Clear the buffer
                print(f"DEBUG: _send_from_buffer: Done sending, window full or buffer empty.")

    def _send_segment(self, segment, is_retransmission=False):
        try:
            packed_segment = segment.pack()
            if self.simulator:
                self.simulator.sendto(self.sock, packed_segment, self.remote_address)
            else:
                self.sock.sendto(packed_segment, self.remote_address)
        except Exception as e:
            print(f"ERROR: Failed to send segment {segment.seq_num}: {e}")
            traceback.print_exc()

    def _handle_ack_locked(self, ack_num):
        """Handle incoming ACKs."""
        if ack_num > self.send_base:
            now = time.time()
            if ack_num - 1 in self.sent_timestamps:
                rtt_sample = now - self.sent_timestamps[ack_num - 1]
                self.rtt_log.append((now, rtt_sample))
                self.rtt_estimator.update(rtt_sample)

            keys_to_remove = [seq for seq in self.unacked_segments if seq < ack_num]
            for seq in keys_to_remove:
                self.unacked_segments.pop(seq, None)
                self.sent_timestamps.pop(seq, None)

            self.send_base = ack_num
            self.congestion_control.on_ack()
            self.log_cwnd()
            print("DEBUG _handle_ack_locked: Triggering _send_from_buffer after ACK.")

            self._send_from_buffer()

    def _handle_data_locked(self, segment):
        """Handle incoming data segments."""
        if segment.seq_num == self.expected_seq_num:
            self.receive_buffer.extend(segment.data)
            self.expected_seq_num += len(segment.data)
            self._send_ack_locked()
        elif segment.seq_num > self.expected_seq_num:
            self.out_of_order_buffer[segment.seq_num] = segment.data
        else:
            self._send_ack_locked()

    def _send_ack_locked(self):
        """Send an ACK for the next expected sequence number."""
        ack_segment = TCPSegment(
            seq_num=self.seq_num,
            ack_num=self.expected_seq_num,
            flags=TCPSegment.ACK,
            rwnd=self._calculate_rwnd_locked(),
            data=b''
        )
        try:
            if self.simulator:
                self.simulator.sendto(self.sock, ack_segment.pack(), self.remote_address)
            else:
                self.sock.sendto(ack_segment.pack(), self.remote_address)

            print(f"DEBUG _send_ack_locked: Sent ACK to {self.remote_address} with ack={self.expected_seq_num}")
        except Exception as e:
            print(f"ERROR _send_ack_locked: Failed to send ACK: {e}")
            traceback.print_exc()

    def _calculate_rwnd_locked(self):
        occupied = len(self.receive_buffer) + sum(len(d) for d in self.out_of_order_buffer.values())
        available = self.max_receive_buffer_size - occupied
        return max(0, available)

    def close(self):
        with self.lock:
            self.is_running = False
            self.state = self.FIN_WAIT_1  # Update state to FIN_WAIT_1

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join()

        try:
            with open("cwnd_log.json", "w") as f:
                json.dump(self.cwnd_log, f, indent=4)
        except Exception as e:
            print(f"ERROR saving cwnd_log: {e}")

    def _check_timers(self):
        """Check for retransmission timeouts and handle expired segments."""
        now = time.time()
        rto_val = self.rtt_estimator.get_timeout()
        check_rto = max(self.rto, rto_val) if rto_val is not None else self.rto

        self.rto_log.append((now, check_rto))

        expired = []
        with self.lock:
            for seq, ts in self.sent_timestamps.items():
                if now - ts > check_rto:
                    expired.append(seq)

        for seq in expired:
            segment = self.unacked_segments.get(seq)
            if segment:
                print(f"DEBUG: Retransmitting segment {seq} due to timeout.")
                self.congestion_control.on_timeout()  # Trigger congestion control timeout handling
                self.log_cwnd()  # Log the updated congestion window
                self._send_segment(segment, is_retransmission=True)  # Retransmit the segment
                self.retransmitted_segments.add(seq)  # Mark the segment as retransmitted