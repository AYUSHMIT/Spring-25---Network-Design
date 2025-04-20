class TCPSegment:
    def __init__(self, seq_num, ack_num, data, flags, rwnd=0):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data
        self.flags = flags
        self.rwnd = rwnd

    def pack(self, pseudo_header=b''):
        """Pack the TCP segment into bytes, including the checksum."""
        segment_without_checksum = (
            self.seq_num.to_bytes(4, 'big') +
            self.ack_num.to_bytes(4, 'big') +
            self.flags.to_bytes(2, 'big') +
            self.rwnd.to_bytes(2, 'big') +
            b'\x00\x00' +  # Placeholder for checksum
            self.data
        )
        self.checksum = self.calculate_checksum(pseudo_header + segment_without_checksum)
        return (
            self.seq_num.to_bytes(4, 'big') +
            self.ack_num.to_bytes(4, 'big') +
            self.flags.to_bytes(2, 'big') +
            self.rwnd.to_bytes(2, 'big') +
            self.checksum.to_bytes(2, 'big') +
            self.data
        )

    @staticmethod
    def unpack(segment_bytes, pseudo_header=b''):
        """Unpack bytes into a TCP segment and verify the checksum."""
        seq_num = int.from_bytes(segment_bytes[0:4], 'big')
        ack_num = int.from_bytes(segment_bytes[4:8], 'big')
        flags = int.from_bytes(segment_bytes[8:10], 'big')
        rwnd = int.from_bytes(segment_bytes[10:12], 'big')
        checksum = int.from_bytes(segment_bytes[12:14], 'big')
        data = segment_bytes[14:]

        # Verify checksum
        calculated_checksum = TCPSegment.calculate_checksum(
            pseudo_header + segment_bytes[:12] + b'\x00\x00' + data
        )
        if calculated_checksum != checksum:
            raise ValueError("Checksum verification failed!")

        segment = TCPSegment(seq_num, ack_num, data, flags, rwnd)
        segment.checksum = checksum  # Store the checksum in the object
        return segment
    @staticmethod
    def calculate_checksum(segment_bytes):
        """Calculate the checksum for the TCP segment, including pseudo-header if provided."""
        checksum = 0
        for i in range(0, len(segment_bytes), 2):
            if i + 1 < len(segment_bytes):
                word = (segment_bytes[i] << 8) + segment_bytes[i + 1]
            else:
                word = (segment_bytes[i] << 8)
            checksum += word
            checksum = (checksum >> 16) + (checksum & 0xFFFF)  # Fold 32 bits to 16 bits
        return ~checksum & 0xFFFF  # One's complement