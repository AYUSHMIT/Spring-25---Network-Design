import socket
import struct
import random
import time

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

# Define the address and listen_address variables
address = ('localhost', 12345)
listen_address = ('localhost', 12345)
save_path = 'C:/Users/Ayush_Pandey/Dev/RDT/received_image.jpg'

def send_file(file_path, update_fsm_state, option, error_rate, retry_count=3):
    packets = make_packet(file_path)
    sock = create_udp_socket()
    seq_num = 0

    for packet in packets:
        rdt_packet = make_rdt_packet(seq_num, packet)
        try:
            send_packet(sock, rdt_packet, address)
            print(f"Sent packet {seq_num}")
            while True:
                ack_packet, _ = receive_packet(sock)
                ack_seq_num, ack_checksum = parse_ack_packet(ack_packet)
                if ack_seq_num == seq_num and not is_corrupt(ack_packet):
                    print(f"Received ACK for packet {seq_num}")
                    break
        except ConnectionResetError as e:
            print(f"ConnectionResetError: {e}")
            if retry_count > 0:
                print(f"Retrying... {retry_count} attempts left.")
                time.sleep(5)
                send_file(file_path, update_fsm_state, option, error_rate, retry_count - 1)
                return
            else:
                update_fsm_state(f"Error sending packet {seq_num}: {e}")
                return
        except Exception as e:
            print(f"Error sending packet {seq_num}: {e}")
            update_fsm_state(f"Error sending packet {seq_num}: {e}")
            return
        seq_num += 1
        update_fsm_state(f"Sent packet {seq_num}")

    # Send an empty packet to indicate the end of the file transfer
    end_packet = make_rdt_packet(seq_num, b'')
    send_packet(sock, end_packet, address)
    print("Sent end of file packet")
    update_fsm_state("Sent end of file packet")

def receive_file(update_fsm_state, option, error_rate):
    sock = create_udp_socket()
    global listen_address  # Ensure listen_address is accessible
    while True:
        try:
            sock.bind(listen_address)
            break
        except OSError as e:
            if e.errno == 10048:  # Address already in use
                listen_address = ('localhost', random.randint(10000, 20000))
            else:
                raise e

    received_packets = {}
    expected_seq_num = 0

    while True:
        try:
            rdt_packet, sender_address = receive_packet(sock)
            if not is_corrupt(rdt_packet):
                seq_num, _, data = parse_rdt_packet(rdt_packet)
                if seq_num == expected_seq_num:
                    if data == b'':  # End of file packet
                        print("Received end of file packet")
                        update_fsm_state("Received end of file packet")
                        break
                    received_packets[seq_num] = data
                    ack_packet = make_ack_packet(seq_num)
                    send_packet(sock, ack_packet, sender_address)
                    print(f"Received packet {seq_num}")
                    expected_seq_num += 1
                    update_fsm_state(f"Received packet {seq_num}")
                else:
                    ack_packet = make_ack_packet(expected_seq_num - 1)
                    send_packet(sock, ack_packet, sender_address)
            else:
                ack_packet = make_ack_packet(expected_seq_num - 1)
                send_packet(sock, ack_packet, sender_address)
        except Exception as e:
            print(f"Error receiving packet: {e}")
            update_fsm_state(f"Error receiving packet: {e}")
            return

    with open(save_path, 'wb') as f:
        for i in range(expected_seq_num):
            f.write(received_packets[i])
    print("File received successfully")
    update_fsm_state("File received successfully")
    sock.close()