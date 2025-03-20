"""
Author: ChatGPT
Description: Reliable Data Transfer (RDT) protocol simulation over UDP.
This client code implements RDT 2.2 and RDT 3.0 features to reliably send a BMP image file over UDP.
It supports simulation of various error conditions:
    Option 1 - No loss/bit-errors.
    Option 2 - ACK packet bit-error.
    Option 4 - ACK packet loss.
(Options 3 and 5 are implemented on the server side.)
"""

import socket
import struct
import time
import random

# Simulation Option (select one):
#   1 - No loss/bit-errors.
#   2 - ACK packet bit-error.
#   4 - ACK packet loss.
SIMULATION_OPTION = 1

# Set simulation probabilities based on option (client-side relevant)
if SIMULATION_OPTION == 1:
    ACK_BIT_ERROR_PROB = 0.0
    ACK_LOSS_PROB = 0.0
elif SIMULATION_OPTION == 2:
    ACK_BIT_ERROR_PROB = 0.1  # 10% chance to corrupt ACK bit
    ACK_LOSS_PROB = 0.0
elif SIMULATION_OPTION == 4:
    ACK_BIT_ERROR_PROB = 0.0
    ACK_LOSS_PROB = 0.1      # 10% chance to simulate ACK loss
else:
    ACK_BIT_ERROR_PROB = 0.0
    ACK_LOSS_PROB = 0.0

# Client settings
UDP_IP = "127.0.0.1"   # Server address
UDP_PORT = 5005        # Server port
BUFFER_SIZE = 1024     # Packet size in bytes

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

# Read the BMP file to be transferred
with open("image.bmp", "rb") as f:
    file_data = f.read()

# Split the file into fixed-size packets
packets = [file_data[i:i+BUFFER_SIZE] for i in range(0, len(file_data), BUFFER_SIZE)]

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(1)  # Set a 1-second timeout for ACK reception

seq_num = 0
start_time = time.time()  # Start timing the transfer

# Write header to log file
write_log("Packet Log - Client Side")
write_log("Timestamp | Packet # | Action | Checksum | Status")

for packet in packets:
    checksum = check_sum(packet)
    # Create packet header: [4-byte sequence number] + [1-byte checksum]
    header = struct.pack("I B", seq_num, checksum)
    full_packet = header + packet

    while True:
        # Send the packet over UDP
        client_socket.sendto(full_packet, (UDP_IP, UDP_PORT))
        print(f"Sent Packet {seq_num}")
        write_log(f"{time.time()} | {seq_num} | Sent | {checksum} | Success")

        try:
            # Wait for the 4-byte ACK packet from the server
            ack_packet, _ = client_socket.recvfrom(4)
            ack_num = struct.unpack("I", ack_packet)[0]

            # Option 2: Simulate ACK packet bit-error (client side)
            if SIMULATION_OPTION == 2 and random.random() < ACK_BIT_ERROR_PROB:
                ack_num ^= 1  # Flip the least significant bit
                print(f"Simulated ACK bit error: corrupted ACK {ack_num} for Packet {seq_num}")
                write_log(f"{time.time()} | {seq_num} | Resent | {checksum} | Simulated ACK bit error")
                continue

            # Option 4: Simulate ACK packet loss (client side)
            if SIMULATION_OPTION == 4 and random.random() < ACK_LOSS_PROB:
                print(f"Simulated ACK loss for Packet {seq_num}")
                write_log(f"{time.time()} | {seq_num} | Lost | {checksum} | Simulated ACK loss")
                continue

            # Check if the ACK matches the expected sequence number
            if ack_num == seq_num:
                print(f"Received ACK {ack_num} for Packet {seq_num}, sending next packet.")
                seq_num = 1 - seq_num  # Toggle sequence number (for a 2-state protocol)
                break  # Move on to the next packet
            else:
                print(f"Received incorrect ACK {ack_num} for Packet {seq_num}, resending.")
                write_log(f"{time.time()} | {seq_num} | Resent | {checksum} | Incorrect ACK")
                continue
        except socket.timeout:
            print(f"ACK not received for Packet {seq_num}, resending.")
            write_log(f"{time.time()} | {seq_num} | Lost | {checksum} | Timeout")

# Stop timing after the last packet is sent successfully
end_time = time.time()
total_time = end_time - start_time

print("File transfer complete.")
print(f"Time taken to send file: {total_time:.2f} seconds.")
write_log(f"File Transfer Completed in {total_time:.2f} seconds")

# Signal the end of the transfer and close the socket
client_socket.sendto(b"STOP", (UDP_IP, UDP_PORT))
client_socket.close()