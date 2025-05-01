# tcp_segment.py

import struct

# TCP-like header format:
# seq_num (4 bytes) | ack_num (4 bytes) | flags (1 byte) | window (2 bytes) | checksum (2 bytes)
HEADER_FORMAT = "!IIBHH"  # Network byte order (big-endian): 4 + 4 + 1 + 2 + 2 = 13 bytes

def compute_checksum(segment):
    """Compute a 16-bit checksum for the segment."""
    if len(segment) % 2 != 0:
        segment += b'\0'

    checksum = 0
    for i in range(0, len(segment), 2):
        word = (segment[i] << 8) + segment[i+1]
        checksum += word
        checksum = (checksum & 0xffff) + (checksum >> 16)
    checksum = ~checksum & 0xffff
    return checksum

def create_segment(seq_num, ack_num, syn, ack, fin, window, payload):
    """Create a TCP-like segment."""
    flags = (syn << 2) | (ack << 1) | fin
    # Temporary checksum = 0 for initial header
    temp_header = struct.pack(HEADER_FORMAT, seq_num, ack_num, flags, window, 0)
    segment = temp_header + payload
    checksum = compute_checksum(segment)
    # Repack with correct checksum
    header = struct.pack(HEADER_FORMAT, seq_num, ack_num, flags, window, checksum)
    return header + payload

def parse_segment(segment_bytes):
    """Parse a TCP-like segment and return its fields."""
    header = segment_bytes[:13]
    payload = segment_bytes[13:]

    seq_num, ack_num, flags, window, recv_checksum = struct.unpack(HEADER_FORMAT, header)

    # Checksum validation:
    computed_checksum = compute_checksum(segment_bytes)  # Compute checksum on full segment

    return {
        'seq_num': seq_num,
        'ack_num': ack_num,
        'syn': (flags >> 2) & 0x1,
        'ack': (flags >> 1) & 0x1,
        'fin': flags & 0x1,
        'window': window,
        'checksum_valid': (computed_checksum == 0),  # ✅ Correct way
        'payload': payload
    }
