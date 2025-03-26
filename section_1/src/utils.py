import random
import time
import struct

def simulate_loss(probability):
    return random.random() < probability

def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)
        bit_index = random.randint(0, 7)
        byte_array = bytearray(packet)
        byte_array[index] ^= (1 << bit_index)# Flips a random bit
        return bytes(byte_array)
    return packet

def read_bmp_file(file_path):
    with open(file_path, 'rb') as bmp_file:
        return bmp_file.read()

def write_bmp_file(file_path, data):
    with open(file_path, 'wb') as bmp_file:
        bmp_file.write(data)

def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFFFF
    return checksum

def verify_checksum(packet):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)
    header = packet[:header_size]
    data = packet[header_size:-2]
    received_checksum = struct.unpack("!H", packet[-2:])[0]
    calculated_checksum = calculate_checksum(header + data)
    return received_checksum == calculated_checksum

def extract_sequence_number(packet):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)
    header = packet[:header_size]
    seq_num, _, _, _ = struct.unpack(header_format, header)
    return seq_num

def extract_data(packet):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)
    return packet[header_size:-2]

def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)

    if not isinstance(data, bytes):
        data = data.encode()

    checksum_data = packet_type + struct.pack("!II", sequence_number, len(data)) + data
    checksum = calculate_checksum(checksum_data)
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data + struct.pack("!H", checksum)

class Timer:
    def __init__(self):
        self.start_time = None
        self.interval = None

    def start(self, interval):
        self.start_time = time.time()
        self.interval = interval

    def stop(self):
        self.start_time = None
        self.interval = None

    def is_expired(self):
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) > self.interval

    def restart(self):
        self.start(self.interval)