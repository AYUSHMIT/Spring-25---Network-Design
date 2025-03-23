import socket
import struct
import time
import random
import os

# Constants
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

def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)

    if not isinstance(data, bytes):
        data = data.encode()

    checksum_data = packet_type + struct.pack("!II", sequence_number, len(data)) + data
    checksum = calculate_checksum(checksum_data)
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data + struct.pack("!H", checksum)

def simulate_loss(probability):
    return random.random() < probability

def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)
        bit_index = random.randint(0, 7)
        byte_array = bytearray(packet)
        byte_array[index] ^= (1 << bit_index)
        return bytes(byte_array)
    return packet

def rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer):
    if nextsegnum < base + N:
        print(f"Sending packet {nextsegnum}, base={base}, nextsegnum={nextsegnum}, N={N}")
        packet = make_packet(nextsegnum, data)
        sndpkt[nextsegnum % N] = packet
        if not simulate_loss(DATA_LOSS_RATE):
            sock.sendto(packet, address)
        else:
            print(f"Simulating loss of packet {nextsegnum}")

        if base == nextsegnum:
            timer.start(TIMEOUT)
        return nextsegnum + 1
    else:
        print("Refuse data, window is full")
        return nextsegnum

def run_go_back_n_sender(host, port, file_path, N):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    address = (host, port)
    timer = Timer()
    base = 0
    nextsegnum = 0
    sndpkt = [b''] * N

    try:
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(PACKET_SIZE)
                if not data:
                    break
                nextsegnum = rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer)

                while base < nextsegnum:
                    if timer.is_expired():
                        print("Timeout, retransmitting packets")
                        timer.restart()
                        for i in range(base, nextsegnum):
                            if not simulate_loss(DATA_LOSS_RATE):
                                sock.sendto(sndpkt[i % N], address)
                            else:
                                print(f"Simulating loss of packet {i}")
                    ack_num, _, _ = rdt_rcv(sock, N, base)
                    if ack_num is not None:
                        print(f"Received ACK {ack_num}")
                        base = ack_num + 1
                        if base == nextsegnum:
                            timer.stop()
                        else:
                            timer.restart()

                if base >= nextsegnum:
                    break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    sender_host = 'localhost'
    sender_port = 12345
    file_to_transfer = 'example.bmp'
    window_size = 10

    run_go_back_n_sender(sender_host, sender_port, file_to_transfer, window_size)