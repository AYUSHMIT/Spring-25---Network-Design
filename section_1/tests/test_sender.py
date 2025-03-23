import unittest
from unittest.mock import MagicMock, patch
from src.sender import rdt_send
from src.go_back_n import make_packet

class TestSender(unittest.TestCase):

    @patch('src.sender.socket.socket')
    def test_rdt_send_success(self, mock_socket):
        mock_sock = mock_socket.return_value
        address = ('localhost', 12345)
        data = b'Test BMP data'
        base = 0
        nextsegnum = 0
        N = 10
        sndpkt = [b''] * N
        timer = MagicMock()

        # Prepare the packet
        packet = make_packet(nextsegnum, data)
        sndpkt[nextsegnum % N] = packet

        # Simulate sending the packet
        nextsegnum = rdt_send(mock_sock, address, data, base, nextsegnum, N, sndpkt, timer)

        # Check if the packet was sent
        mock_sock.sendto.assert_called_once_with(packet, address)
        self.assertEqual(nextsegnum, 1)

    @patch('src.sender.socket.socket')
    def test_rdt_send_packet_loss(self, mock_socket):
        mock_sock = mock_socket.return_value
        address = ('localhost', 12345)
        data = b'Test BMP data'
        base = 0
        nextsegnum = 0
        N = 10
        sndpkt = [b''] * N
        timer = MagicMock()

        # Simulate packet loss
        with patch('src.sender.simulate_loss', return_value=True):
            nextsegnum = rdt_send(mock_sock, address, data, base, nextsegnum, N, sndpkt, timer)

        # Check that the packet was not sent
        mock_sock.sendto.assert_not_called()
        self.assertEqual(nextsegnum, 1)

    @patch('src.sender.socket.socket')
    def test_rdt_send_with_full_window(self, mock_socket):
        mock_sock = mock_socket.return_value
        address = ('localhost', 12345)
        data = b'Test BMP data'
        base = 0
        nextsegnum = 10  # Simulate a full window
        N = 10
        sndpkt = [b''] * N
        timer = MagicMock()

        nextsegnum = rdt_send(mock_sock, address, data, base, nextsegnum, N, sndpkt, timer)

        # Check that the packet was not sent due to full window
        mock_sock.sendto.assert_not_called()
        self.assertEqual(nextsegnum, 10)

if __name__ == '__main__':
    unittest.main()