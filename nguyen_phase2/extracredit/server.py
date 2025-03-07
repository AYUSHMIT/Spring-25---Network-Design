"""
Author: Joseph Nguyen
Description: This module implements a multi-threaded server for a reliable UDP-based file transfer protocol.
It uses two background threads:
  - A receiver thread that continuously receives UDP packets and enqueues them.
  - A processor thread that dequeues packets, validates them, sends ACKs, reassembles the file,
    and updates the GUI.
GUI updates are performed via QMetaObject.invokeMethod so that they run in the main (GUI) thread,
ensuring thread safety and avoiding segmentation faults.
"""

import socket
import struct
import random
import time
import sys
import threading
import queue
from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
from gui import get_app, ServerFileTransferGUI  # Ensure gui.py defines these

# Network configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
BUFFER_SIZE = 1024
log_file = "log.txt"

def write_log(entry):
    """
    Writes a log entry to the designated log file.
    
    Parameters:
        entry (str): The log entry to write.
    """
    with open(log_file, "a") as f:
        f.write(entry + "\n")

def crc16(data: bytes, poly=0x8005) -> int:
    """
    Computes a 1-byte CRC-16 checksum using the specified polynomial.
    
    Parameters:
        data (bytes): Data to compute the checksum for.
        poly (int): Polynomial for CRC computation (default 0x8005).
    
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

# Thread-safe queue for incoming packets.
packet_queue = queue.Queue()
# Global variables for transfer state.
received_data = {}      # Dictionary to store received packets (keyed by packet count).
expected_seq_num = 0    # Expected sequence number (toggle between 0 and 1).
start_time = None       # Timestamp marking the start of the transfer.
total_packets = None    # Total number of packets to receive (set via a control message).

def receiver(sock: socket.socket):
    """
    Receiver thread: continuously receives UDP packets and enqueues them.
    Also handles control messages (e.g., setting the total packet count).
    """
    global total_packets, start_time
    while True:
        try:
            packet, client_address = sock.recvfrom(BUFFER_SIZE + 5)
        except Exception:
            continue
        # Handle control message indicating total packet count.
        if packet.startswith(b"TOTAL:"):
            try:
                total_packets = int(packet.decode().split(":")[1])
                QMetaObject.invokeMethod(gui, "update_fsm_state",
                                         Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(str, f"Expecting {total_packets} packets."))
            except Exception:
                QMetaObject.invokeMethod(gui, "update_fsm_state",
                                         Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(str, "Error parsing total packets info."))
            continue
        # Enqueue the packet along with the client address.
        packet_queue.put((packet, client_address))
        if packet == b"STOP":
            break

def processor(sock: socket.socket):
    """
    Processor thread: processes packets from the queue.
    Validates packets, sends ACKs, updates progress and reassembles the file.
    GUI updates (e.g., progress, FSM state, and image preview) are queued to run in the main thread.
    """
    global expected_seq_num, start_time
    packet_count = 0
    while True:
        try:
            packet, client_address = packet_queue.get(timeout=1)
        except queue.Empty:
            continue
        # Termination signal from client.
        if packet == b"STOP":
            if start_time:
                total_time = time.time() - start_time
                QMetaObject.invokeMethod(gui, "update_fsm_state",
                                         Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(str, f"File Transfer Complete. Time: {total_time:.2f} seconds"))
                write_log(f"File Transfer Completed in {total_time:.2f} seconds")
            break
        if start_time is None:
            start_time = time.time()
        if len(packet) < 5:
            continue
        # Unpack packet header: a 4-byte sequence number and a 1-byte checksum.
        seq_num, received_checksum = struct.unpack("I B", packet[:5])
        data = packet[5:]
        computed_checksum = crc16(data)
        # Validate packet.
        if computed_checksum == received_checksum and seq_num == expected_seq_num:
            received_data[packet_count] = data
            write_log(f"{time.time()} | {seq_num} | Received | {computed_checksum} | Success")
            time.sleep(random.uniform(0, 0.5))  # Simulated network delay.
            # Send ACK.
            ack_packet = struct.pack("I", seq_num)
            sock.sendto(ack_packet, client_address)
            expected_seq_num = 1 - expected_seq_num  # Toggle sequence number.
            packet_count += 1
            # Update progress in GUI.
            if total_packets:
                QMetaObject.invokeMethod(gui, "update_progress",
                                         Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(int, packet_count), Q_ARG(int, total_packets))
            else:
                QMetaObject.invokeMethod(gui, "update_progress",
                                         Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(int, packet_count), Q_ARG(int, 1))
            QMetaObject.invokeMethod(gui, "update_fsm_state",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, f"Received Packet {seq_num} (Packet {packet_count})"))
            # Reassemble file data in order.
            sorted_data = b"".join(received_data[i] for i in sorted(received_data.keys()))
            with open("received_image.jpg", "wb") as f:
                f.write(sorted_data)
            QMetaObject.invokeMethod(gui, "update_image",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, "received_image.jpg"))
        else:
            write_log(f"{time.time()} | {seq_num} | Corrupt | {computed_checksum} | Resent ACK")
            time.sleep(random.uniform(0, 0.5))
            ack_packet = struct.pack("I", 1 - expected_seq_num)
            sock.sendto(ack_packet, client_address)
            QMetaObject.invokeMethod(gui, "update_fsm_state",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, f"Corrupt Packet {seq_num}, resent ACK"))
    sock.close()

def main():
    """
    Main server function that initializes the UDP socket,
    starts the receiver and processor threads, and waits for them to finish.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((UDP_IP, UDP_PORT))
    
    # Start the receiver thread.
    recv_thread = threading.Thread(target=receiver, args=(server_socket,), daemon=True)
    recv_thread.start()
    # Start the processor thread.
    proc_thread = threading.Thread(target=processor, args=(server_socket,), daemon=True)
    proc_thread.start()
    
    recv_thread.join()
    proc_thread.join()
    server_socket.close()

# Initialize the GUI in the main thread.
app = get_app()
gui = ServerFileTransferGUI()

# Start the server's main function in a separate thread.
server_thread = threading.Thread(target=main, daemon=True)
server_thread.start()

# Run the Qt event loop in the main thread.
app.exec()

#File Transfer Complete. Time: 378.31 seconds 