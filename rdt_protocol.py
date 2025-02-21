import os
import socket
import struct
import random
import time
import matplotlib.pyplot as plt
import threading

def make_packet(file_path, packet_size=1024):
    packets = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(packet_size)
            if not chunk:
                break
            packets.append(chunk)
    return packets

def create_udp_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_packet(sock, packet, address):
    sock.sendto(packet, address)

def receive_packet(sock, buffer_size=1030):  # Increased buffer size to 1030 (1024 + 6 for header)
    return sock.recvfrom(buffer_size)

def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFF  # Keep it 8-bit
    return ~checksum & 0xFF

def make_rdt_packet(seq_num, data):
    checksum = calculate_checksum(data)
    header = struct.pack('!I B', seq_num, checksum)
    return header + data

def parse_rdt_packet(packet):
    header = packet[:5]
    data = packet[5:]
    seq_num, checksum = struct.unpack('!I B', header)
    return seq_num, checksum, data

def is_corrupt(packet):
    seq_num, checksum, data = parse_rdt_packet(packet)
    return calculate_checksum(data) != checksum

def make_ack_packet(seq_num):
    checksum = calculate_checksum(struct.pack('!I', seq_num))
    return struct.pack('!I B', seq_num, checksum)

def parse_ack_packet(packet):
    return struct.unpack('!I B', packet)

def rdt_send(file_path, address):
    packets = make_packet(file_path)
    sock = create_udp_socket()
    seq_num = 0

    for packet in packets:
        rdt_packet = make_rdt_packet(seq_num, packet)
        send_packet(sock, rdt_packet, address)
        while True:
            ack_packet, _ = receive_packet(sock)
            ack_seq_num, ack_checksum = parse_ack_packet(ack_packet)
            if ack_seq_num == seq_num and not is_corrupt(ack_packet):
                break
        seq_num += 1

def rdt_receive(save_path, listen_address):
    sock = create_udp_socket()
    sock.bind(listen_address)
    received_packets = {}
    expected_seq_num = 0

    while True:
        rdt_packet, sender_address = receive_packet(sock)
        if not is_corrupt(rdt_packet):
            seq_num, _, data = parse_rdt_packet(rdt_packet)
            if seq_num == expected_seq_num:
                received_packets[seq_num] = data
                ack_packet = make_ack_packet(seq_num)
                send_packet(sock, ack_packet, sender_address)
                expected_seq_num += 1
            else:
                ack_packet = make_ack_packet(expected_seq_num - 1)
                send_packet(sock, ack_packet, sender_address)
        else:
            ack_packet = make_ack_packet(expected_seq_num - 1)
            send_packet(sock, ack_packet, sender_address)

        if len(received_packets) * 1024 >= 500 * 1024:  # Assuming 500KB file
            break

    with open(save_path, 'wb') as f:
        for i in range(expected_seq_num):
            f.write(received_packets[i])

def introduce_bit_error(packet):
    byte_list = list(packet)
    index = random.randint(0, len(byte_list) - 1)
    byte_list[index] ^= 0xFF  # Flip all bits in the byte
    return bytes(byte_list)

def rdt_send_with_errors(file_path, address, error_type=None):
    packets = make_packet(file_path)
    sock = create_udp_socket()
    seq_num = 0

    for packet in packets:
        rdt_packet = make_rdt_packet(seq_num, packet)
        if error_type == 'data' and random.random() < 0.1:  # 10% chance of error
            rdt_packet = introduce_bit_error(rdt_packet)
        send_packet(sock, rdt_packet, address)
        while True:
            ack_packet, _ = receive_packet(sock)
            if error_type == 'ack' and random.random() < 0.1:  # 10% chance of error
                ack_packet = introduce_bit_error(ack_packet)
            ack_seq_num, ack_checksum = parse_ack_packet(ack_packet)
            if ack_seq_num == seq_num and not is_corrupt(ack_packet):
                break
        seq_num += 1

def measure_completion_time(file_path, address, error_type=None):
    start_time = time.time()
    rdt_send_with_errors(file_path, address, error_type)
    end_time = time.time()
    return end_time - start_time

def plot_performance():
    file_path = 'C:/Users/Ayush_Pandey/Dev/RDT/phase_2.jpg'  # Update this path
    address = ('localhost', 12345)
    error_rates = [i for i in range(0, 65, 5)]
    completion_times = {'no_error': [], 'ack_error': [], 'data_error': []}

    for error_rate in error_rates:
        completion_times['no_error'].append(measure_completion_time(file_path, address))
        completion_times['ack_error'].append(measure_completion_time(file_path, address, 'ack'))
        completion_times['data_error'].append(measure_completion_time(file_path, address, 'data'))

    plt.plot(error_rates, completion_times['no_error'], label='No Error')
    plt.plot(error_rates, completion_times['ack_error'], label='ACK Error')
    plt.plot(error_rates, completion_times['data_error'], label='Data Error')
    plt.xlabel('Error Rate (%)')
    plt.ylabel('Completion Time (s)')
    plt.legend()
    plt.show()

def start_receiver():
    save_path = 'C:/Users/Ayush_Pandey/Dev/RDT/received_image.jpg'  # Update this path if needed
    listen_address = ('localhost', 12345)
    rdt_receive(save_path, listen_address)

def start_sender():
    file_path = 'C:/Users/Ayush_Pandey/Dev/RDT/phase_2.jpg'  # Update this path
    address = ('localhost', 12345)
    rdt_send_with_errors(file_path, address, error_type=None)  # Change error_type as needed

if __name__ == '__main__':
    receiver_thread = threading.Thread(target=start_receiver)
    receiver_thread.start()
    time.sleep(1)  # Give the receiver some time to start
    start_sender()
    plot_performance()