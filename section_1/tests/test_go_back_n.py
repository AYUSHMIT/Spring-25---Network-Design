import unittest
from src.go_back_n import calculate_checksum, verify_checksum, make_packet, extract_sequence_number, extract_data, extract_packet_type

class TestGoBackN(unittest.TestCase):

    def test_calculate_checksum(self):
        data = b'Test data for checksum'
        checksum = calculate_checksum(data)
        self.assertIsInstance(checksum, int)
        self.assertGreaterEqual(checksum, 0)
        self.assertLessEqual(checksum, 65535)

    def test_verify_checksum_valid(self):
        data = b'Test data for checksum'
        checksum = calculate_checksum(data)
        packet = make_packet(0, data)
        self.assertTrue(verify_checksum(packet))

    def test_verify_checksum_invalid(self):
        data = b'Test data for checksum'
        packet = make_packet(0, data)
        corrupted_packet = bytearray(packet)
        corrupted_packet[0] ^= 1  # Introduce an error
        self.assertFalse(verify_checksum(bytes(corrupted_packet)))

    def test_make_packet(self):
        data = b'Test packet data'
        packet = make_packet(1, data)
        self.assertEqual(extract_sequence_number(packet), 1)
        self.assertEqual(extract_data(packet), data)

    def test_extract_packet_type(self):
        data = b'Test packet data'
        packet = make_packet(1, data)
        self.assertEqual(extract_packet_type(packet), b'DATA')

if __name__ == '__main__':
    unittest.main()