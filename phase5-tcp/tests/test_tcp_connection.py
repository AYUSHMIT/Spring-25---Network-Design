import unittest
from src.tcp_connection import SimpleTCPConnection
from unittest.mock import patch, MagicMock
import time

class TestSimpleTCPConnection(unittest.TestCase):

    def setUp(self):
        self.tcp_connection = SimpleTCPConnection()

    def test_connection_establishment(self):
        """Test the establishment of a TCP connection."""
        self.tcp_connection.connect(('127.0.0.1', 8080))
        self.assertEqual(self.tcp_connection.state, 'SYN_SENT')

    def test_data_transmission(self):
        """Test sending and receiving data."""
        self.tcp_connection.state = 'ESTABLISHED'
        data_to_send = b'Test data'
        self.tcp_connection.send_buffer = data_to_send
        self.tcp_connection.send(data_to_send)
        self.assertEqual(self.tcp_connection.send_buffer, b'')  # Ensure buffer is cleared

    def test_connection_closure(self):
        """Test closing the TCP connection."""
        self.tcp_connection.state = 'ESTABLISHED'
        self.tcp_connection.close()
        self.assertEqual(self.tcp_connection.state, 'FIN_WAIT_1')

    def test_retransmission_logic(self):
        """Test retransmission logic in _check_timers."""
        self.tcp_connection.state = 'ESTABLISHED'
        self.tcp_connection.unacked_segments = {1: b'Segment 1'}
        self.tcp_connection.sent_timestamps = {1: time.time() - 2}  # Simulate timeout
        with patch('src.tcp_connection.SimpleTCPConnection._send_raw_segment') as mock_send:
            self.tcp_connection._check_timers()
            mock_send.assert_called_once_with(b'Segment 1')

    def test_karns_algorithm(self):
        """Test Karn's algorithm for RTT estimation."""
        self.tcp_connection.state = 'ESTABLISHED'
        self.tcp_connection.sent_timestamps = {1: time.time()}
        self.tcp_connection.unacked_segments = {1: b'Segment 1'}
        with patch('src.rtt_estimator.RTTEstimator.update') as mock_update:
            self.tcp_connection._handle_ack(ack_num=2)
            mock_update.assert_called_once()  # Ensure RTT is updated

    def test_window_size_calculation(self):
        """Test window size calculation in _send_window."""
        self.tcp_connection.cwnd = 512
        self.tcp_connection.peer_rwnd = 1024
        effective_window = self.tcp_connection._send_window()
        self.assertEqual(effective_window, 512)

    def test_congestion_control_on_ack(self):
        """Test congestion control integration on ACK."""
        self.tcp_connection.state = 'ESTABLISHED'
        with patch('src.congestion_control.CongestionControl.on_ack_received') as mock_on_ack:
            self.tcp_connection._handle_ack(ack_num=1)
            mock_on_ack.assert_called_once()

    def test_congestion_control_on_timeout(self):
        """Test congestion control integration on timeout."""
        self.tcp_connection.state = 'ESTABLISHED'
        with patch('src.congestion_control.CongestionControl.on_timeout') as mock_on_timeout:
            self.tcp_connection._check_timers()
            mock_on_timeout.assert_called_once()

    def test_receive_data(self):
        """Test receiving data and appending to the receive buffer."""
        self.tcp_connection.state = 'ESTABLISHED'
        self.tcp_connection._handle_data(b'Test data')
        self.assertEqual(self.tcp_connection.receive_buffer, b'Test data')

    def test_acknowledgment_handling(self):
        """Test handling of ACKs and updating send_base."""
        self.tcp_connection.state = 'ESTABLISHED'
        self.tcp_connection.send_base = 0
        self.tcp_connection.unacked_segments = {1: b'Segment 1', 2: b'Segment 2'}
        self.tcp_connection._handle_ack(ack_num=2)
        self.assertEqual(self.tcp_connection.send_base, 2)
        self.assertNotIn(1, self.tcp_connection.unacked_segments)

if __name__ == '__main__':
    unittest.main()