import unittest
from unittest.mock import patch, MagicMock
from src.sender import rdt_send, make_packet

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

if __name__ == '__main__':
    unittest.main()