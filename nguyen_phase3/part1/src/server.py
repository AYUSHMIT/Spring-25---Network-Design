"""
Author: ChatGPT
Description: Reliable Data Transfer (RDT) protocol simulation over UDP.
This server code implements RDT 2.2 and RDT 3.0 features to reliably receive a BMP image file over UDP.
It supports simulation of various error conditions:
    Option 1 - No loss/bit-errors.
    Option 3 - Data packet bit-error.
    Option 5 - Data packet loss.
(Options 2 and 4 are implemented on the client side.)
"""

import socket
import struct
import random
import time

# Simulation Option (select one):
#   1 - No loss/bit-errors.
#   3 - Data packet bit-error.
#   5 - Data packet loss.
SIMULATION_OPTION = 1

# Set simulation probabilities based on option (server-side relevant)
if SIMULATION_OPTION == 1:
    DATA_BIT_ERROR_PROB = 0.0
    DATA_LOSS_PROB = 0.0
elif SIMULATION_OPTION == 3:
    DATA_BIT_ERROR_PROB = 0.1  # 10% chance to corrupt data packet bits
    DATA_LOSS_PROB = 0.0
elif SIMULATION_OPTION == 5:
    DATA_BIT_ERROR_PROB = 0.0
    DATA_LOSS_PROB = 0.1      # 10% chance to drop data packet
else:
    DATA_BIT_ERROR_PROB = 0.0
    DATA_LOSS_PROB = 0.0

# Server settings
UDP_IP = "127.0.0.1"  # Localhost
UDP_PORT = 5005       # Port to listen on
BUFFER_SIZE = 1024    # Expected packet data size in bytes

# Log file path
log_file = "log.txt"

def write_log(entry):
    """Appends a log entry to log.txt."""
    with open(log_file, "a") as f:
        f.write(entry + "\n")

def check_sum(data):
    """Calculates a simple XOR-based checksum over the data bytes."""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum

# Create and bind a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((UDP_IP, UDP_PORT))
print(f"UDP Server listening on {UDP_IP}:{UDP_PORT}...")

while True:
    received_data = {}  # Dictionary to hold received packets (keyed by sequence number)
    expected_seq_num = 0  # Start expecting sequence number 0
    start_time = None     # Timer starts when the first packet is received

    print("\nWaiting for a new file transfer...")
    write_log("Packet Log - Server Side")
    write_log("Timestamp | Packet # | Action | Checksum | Status")

    while True:
        packet, client_address = server_socket.recvfrom(BUFFER_SIZE + 5)  # 4 bytes for seq + 1 byte for checksum

        # If a STOP message is received, complete the transfer
        if packet == b"STOP":
            if start_time is not None:
                end_time = time.time()
                total_time = end_time - start_time
                print("\nFile transfer complete.")
                print(f"Time taken: {total_time:.2f} seconds.")
                write_log(f"File Transfer Completed in {total_time:.2f} seconds")
            break

        # Start the timer when the first packet is received
        if start_time is None:
            start_time = time.time()

        # Ensure the packet is at least 5 bytes long
        if len(packet) < 5:
            continue

        # Unpack the header: 4-byte sequence number and 1-byte checksum
        seq_num, received_checksum = struct.unpack("I B", packet[:5])
        data = packet[5:]

        # Option 5: Simulate data packet loss (server side)
        if SIMULATION_OPTION == 5 and random.random() < DATA_LOSS_PROB:
            print(f"Simulated data packet loss for Packet {seq_num}")
            write_log(f"{time.time()} | {seq_num} | Dropped | N/A | Simulated Data loss")
            continue  # Do not process or ACK this packet

        # Option 3: Simulate data packet bit-error (server side)
        if SIMULATION_OPTION == 3 and random.random() < DATA_BIT_ERROR_PROB:
            if len(data) > 0:
                # Flip all bits of the first byte to simulate corruption
                corrupted_byte = data[0] ^ 0xFF
                data = bytes([corrupted_byte]) + data[1:]
            print(f"Simulated data bit error for Packet {seq_num}")
            write_log(f"{time.time()} | {seq_num} | Received | {received_checksum} | Simulated Data bit error")

        computed_checksum = check_sum(data)

        # Validate packet integrity and order
        if computed_checksum == received_checksum and seq_num == expected_seq_num:
            received_data[seq_num] = data
            print(f"Received Packet {seq_num}, sending ACK.")
            write_log(f"{time.time()} | {seq_num} | Received | {computed_checksum} | Success")

            # Send ACK with the correct sequence number
            ack_packet = struct.pack("I", seq_num)
            server_socket.sendto(ack_packet, client_address)
            expected_seq_num = 1 - expected_seq_num  # Toggle expected sequence number
        else:
            print(f"Corrupt or out-of-order Packet {seq_num}, resending last ACK.")
            write_log(f"{time.time()} | {seq_num} | Error | {computed_checksum} | Resent ACK")
            # Resend the last valid ACK (using the toggled expected sequence number)
            last_ack = 1 - expected_seq_num
            ack_packet = struct.pack("I", last_ack)
            server_socket.sendto(ack_packet, client_address)

    # Assemble and save the received file after the transfer ends
    if received_data:
        # For a two-state protocol, simply ordering by key (0 and 1) works; adjust if using larger sequence space.
        sorted_data = b"".join(received_data[i] for i in sorted(received_data.keys()))
        with open("received_image.bmp", "wb") as f:
            f.write(sorted_data)
        print("File saved as 'received_image.bmp'")