"""
Author: Joseph Nguyen
Description: This module implements the client side of the reliable file transfer over UDP.
It reads an image file (e.g., JPEG), splits it into packets, and transmits the data with random delays 
and an adaptive timeout mechanism. Before sending the file, it sends a control message indicating the total 
number of packets. This client runs headless and logs all events to the console and a log file.
"""

import socket
import struct
import time
import random
import sys

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
BUFFER_SIZE = 1024
log_file = "log.txt"

def write_log(entry):
    """
    Writes a log entry to the log file.
    
    Parameters:
        entry (str): The message to be logged.
    """
    with open(log_file, "a") as f:
        f.write(entry + "\n")

def crc16(data: bytes, poly=0x8005):
    """
    Computes a 1-byte CRC-16 checksum for the given data.
    
    Parameters:
        data (bytes): The data for which the checksum is computed.
        poly (int): The polynomial to use for CRC computation (default 0x8005).
    
    Returns:
        int: The lower 8 bits of the computed CRC-16 checksum.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
    return crc & 0xFF

# Adaptive timeout parameters for RTT estimation.
alpha = 0.125
beta = 0.25
estimated_RTT = 1.0  # Initial RTT estimate in seconds.
dev_RTT = 0.5
adaptive_timeout = estimated_RTT + 4 * dev_RTT

def send_packets(file_path):
    """
    Splits the image file into packets and sends them to the server.
    Uses random delays to simulate network latency and adapts the timeout based on measured RTT.
    
    Parameters:
        file_path (str): Path to the image file to send.
    """
    global estimated_RTT, dev_RTT, adaptive_timeout
    # Read the image file in binary mode.
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    # Split the file into fixed-size packets.
    packets = [file_data[i:i+BUFFER_SIZE] for i in range(0, len(file_data), BUFFER_SIZE)]
    total_packets = len(packets)
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Send a control message to the server with the total number of packets.
    control_message = f"TOTAL:{total_packets}"
    client_socket.sendto(control_message.encode(), (UDP_IP, UDP_PORT))
    
    seq_num = 0
    start_time = None
    
    write_log("Packet Log - Client Side")
    write_log("Timestamp | Packet # | Action | Checksum | Status")
    
    for i, packet in enumerate(packets):
        checksum = crc16(packet)
        # Pack header: 4-byte sequence number and 1-byte checksum.
        header = struct.pack("I B", seq_num, checksum)
        full_packet = header + packet
        
        while True:
            # Simulate network latency with a random delay (0-500ms).
            time.sleep(random.uniform(0, 0.5))
            
            if start_time is None:
                start_time = time.time()
            
            send_time = time.time()
            client_socket.sendto(full_packet, (UDP_IP, UDP_PORT))
            print(f"Sent Packet {seq_num}")
            write_log(f"{time.time()} | {seq_num} | Sent | {checksum} | Success")
            
            try:
                client_socket.settimeout(adaptive_timeout)
                ack_packet, _ = client_socket.recvfrom(4)
                recv_time = time.time()
                ack_num = struct.unpack("I", ack_packet)[0]
                
                # Update RTT estimates and adjust the adaptive timeout.
                sample_RTT = recv_time - send_time
                estimated_RTT = (1 - alpha) * estimated_RTT + alpha * sample_RTT
                dev_RTT = (1 - beta) * dev_RTT + beta * abs(sample_RTT - estimated_RTT)
                adaptive_timeout = estimated_RTT + 4 * dev_RTT
                
                if ack_num == seq_num:
                    seq_num = 1 - seq_num  # Toggle sequence number.
                    print(f"Progress: {i+1}/{total_packets} packets sent")
                    break  # Proceed to the next packet.
                else:
                    write_log(f"{time.time()} | {seq_num} | Resent | {checksum} | Incorrect ACK")
            except socket.timeout:
                write_log(f"{time.time()} | {seq_num} | Lost | {checksum} | Timeout")
    
    if start_time is not None:
        total_time = time.time() - start_time
        print(f"File Transfer Complete. Time: {total_time:.2f} seconds")
        write_log(f"File Transfer Completed in {total_time:.2f} seconds")
    
    # Signal the server to stop receiving.
    client_socket.sendto(b"STOP", (UDP_IP, UDP_PORT))
    client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <image_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    send_packets(file_path)