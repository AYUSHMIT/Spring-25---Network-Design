import unittest
from src.tcp_segment import TCPSegment

class TestTCPSegment(unittest.TestCase):

    def test_create_segment(self):
        """Test creating a TCP segment."""
        segment = TCPSegment(seq_num=1, ack_num=0, data=b'Test data', rwnd=1024)
        self.assertEqual(segment.seq_num, 1)
        self.assertEqual(segment.ack_num, 0)
        self.assertEqual(segment.data, b'Test data')
        self.assertEqual(segment.rwnd, 1024)

    def test_pack_and_unpack_segment(self):
        """Test packing and unpacking a TCP segment."""
        pseudo_header = b'\x01\x02\x03\x04\x05\x06\x00\x06\x00\x14'  # Example pseudo-header
        segment = TCPSegment(seq_num=1, ack_num=0, data=b'Test data', rwnd=1024)
        packed_segment = segment.pack(pseudo_header=pseudo_header)
        unpacked_segment = TCPSegment.unpack(packed_segment, pseudo_header=pseudo_header)
        self.assertEqual(unpacked_segment.seq_num, 1)
        self.assertEqual(unpacked_segment.ack_num, 0)
        self.assertEqual(unpacked_segment.data, b'Test data')
        self.assertEqual(unpacked_segment.rwnd, 1024)

    def test_checksum(self):
        """Test checksum calculation and validation."""
        pseudo_header = b'\x01\x02\x03\x04\x05\x06\x00\x06\x00\x14'  # Example pseudo-header
        segment = TCPSegment(seq_num=1, ack_num=0, data=b'Test data', rwnd=1024)
        packed_segment = segment.pack(pseudo_header=pseudo_header)
        unpacked_segment = TCPSegment.unpack(packed_segment, pseudo_header=pseudo_header)
        self.assertEqual(segment.checksum, unpacked_segment.checksum)

    def test_invalid_checksum(self):
        """Test detection of an invalid checksum."""
        pseudo_header = b'\x01\x02\x03\x04\x05\x06\x00\x06\x00\x14'  # Example pseudo-header
        segment = TCPSegment(seq_num=1, ack_num=0, data=b'Test data', rwnd=1024)
        packed_segment = segment.pack(pseudo_header=pseudo_header)

        # Corrupt the packed segment
        corrupted_segment = packed_segment[:10] + b'\xFF\xFF' + packed_segment[12:]
        with self.assertRaises(ValueError):
            TCPSegment.unpack(corrupted_segment, pseudo_header=pseudo_header)

if __name__ == '__main__':
    unittest.main()