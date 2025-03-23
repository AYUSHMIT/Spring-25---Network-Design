import socket
import struct
import time
import random

PACKET_SIZE = 1024
TIMEOUT = 0.05
MAX_WINDOW_SIZE = 50
ACK_SIGNAL = b'ACK'
DATA_LOSS_RATE = 0.2
ACK_LOSS_RATE = 0.2
BIT_ERROR_RATE = 0.1

def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFFFF
    return checksum

def verify_checksum(packet):
    received_checksum = struct.unpack("!H", packet[-2:])[0]
    data = packet[:-2]
    calculated_checksum = calculate_checksum(data)
    return calculated_checksum == received_checksum

def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)

    if not isinstance(data, bytes):
        data = data.encode()

    checksum_data = packet_type + struct.pack("!II", sequence_number, len(data)) + data
    checksum = calculate_checksum(checksum_data)
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data + struct.pack("!H", checksum)

def extract_sequence_number(packet):
    return struct.unpack("!I", packet[:4])[0]

def extract_data(packet):
    data_length = struct.unpack("!I", packet[4:8])[0]
    return packet[12:12 + data_length]

def extract_packet_type(packet):
    return packet[8:12]

def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)
        bit_index = random.randint(0, 7)
        byte_array = bytearray(packet)
        byte_array[index] ^= (1 << bit_index)
        return bytes(byte_array)
    return packet

def simulate_loss(probability):
    return random.random() < probability

class Timer:
    def __init__(self):
        self.start_time = 0
        self.running = False

    def start(self, duration):
        self.duration = duration
        self.start_time = time.time()
        self.running = True

    def stop(self):
        self.running = False
        self.start_time = 0

    def is_expired(self):
        if not self.running:
            return False
        return time.time() - self.start_time > self.duration

    def restart(self):
        self.start_time = time.time()
        self.running = True

def rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer):
    if nextsegnum < base + N:
        print(f"rdt_send: Sending packet {nextsegnum}, base={base}, nextsegnum={nextsegnum}, N={N}")
        packet = make_packet(nextsegnum, data)
        sndpkt[nextsegnum % N] = packet
        if not simulate_loss(DATA_LOSS_RATE):
            sock.sendto(packet, address)
        else:
            print(f"rdt_send: Simulating loss of packet {nextsegnum}")

        if base == nextsegnum:
            timer.start(TIMEOUT)
        return nextsegnum + 1
    else:
        print("rdt_send: Refuse data, window is full")
        return nextsegnum

def rdt_rcv(sock, N, expectedsegnum):
    try:
        packet, address = sock.recvfrom(4096)
        if not packet:
            return None, None, expectedsegnum

    except socket.timeout:
        return None, None, expectedsegnum

    if not simulate_loss(DATA_LOSS_RATE):
        packet = introduce_bit_error(packet, BIT_ERROR_RATE)

    if not verify_checksum(packet):
        print("rdt_rcv: Checksum error, discarding packet")
        ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
        sock.sendto(ack_packet, address)
        return None, address, expectedsegnum

    seq_num = extract_sequence_number(packet)
    packet_type = extract_packet_type(packet)

    if packet_type == ACK_SIGNAL:
        return seq_num, address, expectedsegnum

    if seq_num == expectedsegnum:
        print(f"rdt_rcv: Received expected packet {seq_num}")
        data = extract_data(packet)
        ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
        if not simulate_loss(ACK_LOSS_RATE):
            sock.sendto(ack_packet, address)
        else:
            print(f"rdt_rcv: Simulating loss of ACK for packet {expectedsegnum}")
        return data, address, expectedsegnum + 1
    else:
        print(f"rdt_rcv: Out-of-order packet {seq_num}, expected {expectedsegnum}")
        ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
        sock.sendto(ack_packet, address)
        return None, address, expectedsegnum

def run_go_back_n_sender(host, port, file_path, N):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    address = (host, port)
    timer = Timer()
    base = 0
    nextsegnum = 0
    sndpkt = [b''] * N
    file_size = 0

    try:
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(PACKET_SIZE)
                if not data:
                    break
                file_size += len(data)
                nextsegnum = rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer)

                while base < nextsegnum:
                    if timer.is_expired():
                        print("Sender: Timeout, retransmitting packets")
                        timer.restart()
                        for i in range(base, nextsegnum):
                            if not simulate_loss(DATA_LOSS_RATE):
                                sock.sendto(sndpkt[i % N], address)
                            else:
                                print(f"run_go_back_n_sender: Simulating loss of packet {i}")
                    ack_num, _, _ = rdt_rcv(sock, N, base)
                    if ack_num is not None:
                        print(f"Sender: Received ACK {ack_num}")
                        base = ack_num + 1
                        if base == nextsegnum:
                            timer.stop()
                        else:
                            timer.restart()

                if base >= nextsegnum:
                    break

    except Exception as e:
        print(f"Sender: An error occurred: {e}")
    finally:
        sock.close()
    return file_size

def run_go_back_n_receiver(host, port, output_file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    expectedsegnum = 0
    received_data = b''

    try:
        with open(output_file, 'wb') as file:
            while True:
                data, _, expectedsegnum = rdt_rcv(sock, 1, expectedsegnum)
                if data:
                    received_data += data
                    file.write(data)
                    if len(received_data) % (1024 * 100) == 0:
                        print(f"Received {len(received_data)} bytes")
                elif data is None:
                    break

    except Exception as e:
        print(f"Receiver: An error occurred: {e}")
    finally:
        sock.close()
    return len(received_data)