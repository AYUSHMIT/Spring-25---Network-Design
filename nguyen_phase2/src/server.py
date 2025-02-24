import socket
import struct
import random
import time

# Server settings
UDP_IP = "127.0.0.1"  # Localhost
UDP_PORT = 5005       # Port to listen on
BUFFER_SIZE = 1024    # Fixed packet size

# Log file
log_file = "log.txt"

def write_log(entry):
    """Writes log entries to log.txt"""
    with open(log_file, "a") as f:
        f.write(entry + "\n")

def check_sum(data):
    checksum = 0
    for byte in data:
        checksum ^= byte  # XOR on all bytes
    return checksum

# Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((UDP_IP, UDP_PORT))

print(f"UDP Server listening on {UDP_IP}:{UDP_PORT}...")

while True:
    received_data = {}
    expected_seq_num = 0  # Start expecting sequence number 0.
    start_time = None  # Ensure timer starts only when first packet is received

    print("\nWaiting for a new file transfer...")

    # Log file header
    write_log("Packet Log - Server Side")
    write_log("Timestamp | Packet # | Action | Checksum | Status")

    while True:
        packet, client_address = server_socket.recvfrom(BUFFER_SIZE + 5)  # 4-byte seq + 1-byte checksum

        # If the client sends "STOP", break out of the loop, print time taken
        if packet == b"STOP":
            if start_time is not None:  # Ensure timing was recorded
                end_time = time.time()  # Stop timing after last processed packet
                total_time = end_time - start_time
                print("\nFile Transfer complete.")
                print(f"Time completed was {total_time:.2f} seconds.")
                write_log(f"File Transfer Completed in {total_time:.2f} seconds")
            break  

        # Start timing when the first packet is received
        if start_time is None:
            start_time = time.time()

        # Ensure packet has at least 5 bytes before unpacking
        if len(packet) < 5:
            continue  # Ignore and wait for a new packet

        seq_num, received_checksum = struct.unpack("I B", packet[:5])  # Extract the header
        data = packet[5:]  # Extract data
        computed_checksum = check_sum(data)

        # Validating the Checksum
        if computed_checksum == received_checksum and seq_num == expected_seq_num:
            received_data[seq_num] = data
            print(f"Received Packet {seq_num}, sending ACK")
            write_log(f"{time.time()} | {seq_num} | Received | {computed_checksum} | Success")

            # Simulate High Packet Loss
            ack_num = seq_num
            if random.random() < 0.6:  # % probability of corruption
                ack_num ^= 1  # Flip the least significant bit (random error)
                print(f"Corrupt ACK Sent for Packet {seq_num}")
                write_log(f"{time.time()} | {seq_num} | Corrupt ACK | {computed_checksum} | Resent ACK")

            # Send the ACK packet
            ack_packet = struct.pack("I", ack_num)
            server_socket.sendto(ack_packet, client_address)

            expected_seq_num = 1 - expected_seq_num  # Flip sequence number
        else:
            print(f"Corrupt Packet {seq_num}, resending last ACK")
            write_log(f"{time.time()} | {seq_num} | Corrupt Packet | {computed_checksum} | Resent ACK")
            # Resend the last ACK
            ack_packet = struct.pack("I", 1 - expected_seq_num)
            server_socket.sendto(ack_packet, client_address)

    # Assemble and save the received file after exiting the loop
    if received_data:
        sorted_data = b"".join(received_data[i] for i in sorted(received_data.keys()))
        with open("received_image.bmp", "wb") as f:
            f.write(sorted_data)
        print("File saved as `received_image.bmp`")