import socket
import struct
import random
import time
from threading import Thread

# Server settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
BUFFER_SIZE = 1024

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((UDP_IP, UDP_PORT))

print(f"UDP Server listening on {UDP_IP}:{UDP_PORT}...")

received_data = {}
expected_seq_num = 0
start_time = None

log_file = "log.txt"

def write_log(entry):
    """Writes log entries to log.txt"""
    with open(log_file, "a") as f:
        f.write(entry + "\n")

def crc16(data: bytes, poly=0x8005):
    """Compute CRC-16 checksum and return only 1 byte."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
    return crc & 0xFF  # Ensure checksum fits in 1 byte

def receive_packets():
    """Receives packets, logs transmissions, and processes them."""
    global start_time, expected_seq_num

    write_log("Packet Log - Server Side")
    write_log("Timestamp | Packet # | Action | Checksum | Status")

    while True:
        packet, client_address = server_socket.recvfrom(BUFFER_SIZE + 5)

        if packet == b"STOP":
            end_time = time.time()
            total_time = end_time - start_time
            print(f"\nFile Transfer Complete. Time: {total_time:.2f} seconds")
            write_log(f"File Transfer Completed in {total_time:.2f} seconds")
            break  

        if start_time is None:
            start_time = time.time()

        seq_num, received_checksum = struct.unpack("I B", packet[:5])
        data = packet[5:]
        computed_checksum = crc16(data)

        if computed_checksum == received_checksum and seq_num == expected_seq_num:
            received_data[seq_num] = data
            print(f"Received Packet {seq_num}, sending ACK")
            write_log(f"{time.time()} | {seq_num} | Received | {computed_checksum} | Success")

            ack_packet = struct.pack("I", seq_num)
            server_socket.sendto(ack_packet, client_address)
            expected_seq_num = 1 - expected_seq_num
        else:
            print(f"Corrupt Packet {seq_num}, resending last ACK")
            write_log(f"{time.time()} | {seq_num} | Corrupt | {computed_checksum} | Resent ACK")
            ack_packet = struct.pack("I", 1 - expected_seq_num)
            server_socket.sendto(ack_packet, client_address)

recv_thread = Thread(target=receive_packets, daemon=True)
recv_thread.start()
recv_thread.join()

if received_data:
    sorted_data = b"".join(received_data[i] for i in sorted(received_data.keys()))
    with open("received_image.bmp", "wb") as f:
        f.write(sorted_data)
    print("File saved as `received_image.bmp`")