import socket
import struct
import time
import random
import sys
from threading import Thread
from PyQt6.QtWidgets import QApplication
from gui import FileTransferGUI

# Client settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
BUFFER_SIZE = 1024

# Initialize GUI (Runs in Main Thread)
app = QApplication(sys.argv)
gui = FileTransferGUI()

# Log file
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

# Read the BMP file and prepare packets
with open("image.bmp", "rb") as f:
    file_data = f.read()

packets = [file_data[i:i+BUFFER_SIZE] for i in range(0, len(file_data), BUFFER_SIZE)]
total_packets = len(packets)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

seq_num = 0
start_time = None

def send_packets():
    """Handles packet transmission and updates GUI safely."""
    global seq_num, start_time

    write_log("Packet Log - Client Side")
    write_log("Timestamp | Packet # | Action | Checksum | Status")

    for i, packet in enumerate(packets):
        checksum = crc16(packet)
        header = struct.pack("I B", seq_num, checksum)
        full_packet = header + packet

        while True:
            delay = random.uniform(0, 0.1)  # Reduce delay to prevent overflow
            time.sleep(delay)

            if start_time is None:
                start_time = time.time()  # Start timing only when first packet is sent

            client_socket.sendto(full_packet, (UDP_IP, UDP_PORT))
            gui.update_fsm_state(f"Sent Packet {seq_num}")  # GUI FSM Update
            print(f"Sent Packet {seq_num}")
            write_log(f"{time.time()} | {seq_num} | Sent | {checksum} | Success")

            try:
                client_socket.settimeout(1)  # Prevent indefinite waiting
                ack_packet, _ = client_socket.recvfrom(4)
                ack_num = struct.unpack("I", ack_packet)[0]

                if ack_num == seq_num:
                    seq_num = 1 - seq_num  # Flip sequence number
                    gui.update_progress(i + 1, total_packets)  # GUI Progress Update
                    break
                else:
                    print(f"Incorrect ACK {ack_num}, resending Packet {seq_num}.")
                    write_log(f"{time.time()} | {seq_num} | Resent | {checksum} | Incorrect ACK")
                    continue
            except socket.timeout:
                print(f"No ACK received for Packet {seq_num}, resending...")
                write_log(f"{time.time()} | {seq_num} | Lost | {checksum} | Timeout")

    if start_time is not None:
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nFile transfer complete. Time: {total_time:.2f} seconds")
        gui.update_fsm_state("File Transfer Complete")
        write_log(f"File Transfer Completed in {total_time:.2f} seconds")

    client_socket.sendto(b"STOP", (UDP_IP, UDP_PORT))
    client_socket.close()

# Start the packet sending thread (GUI remains in main thread)
send_thread = Thread(target=send_packets, daemon=True)
send_thread.start()

# Run the GUI event loop in the main thread
sys.exit(app.exec())