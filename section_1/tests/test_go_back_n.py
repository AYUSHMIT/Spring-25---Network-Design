import unittest
from src.utils import calculate_checksum, verify_checksum, make_packet, extract_sequence_number, extract_data

class TestGoBackN(unittest.TestCase):
    def test_make_packet(self):
        data = b'Test packet data'
        packet = make_packet(1, data)
        self.assertEqual(extract_sequence_number(packet), 1)
        self.assertEqual(extract_data(packet), data)

    def test_verify_checksum_valid(self):
        data = b'Test data for checksum'
        packet = make_packet(0, data)
        self.assertTrue(verify_checksum(packet))

if __name__ == '__main__':
    unittest.main()