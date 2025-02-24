import socket
import struct
import time
import random 

# Client settings
UDP_IP = "127.0.0.1"  # Server address
UDP_PORT = 5005       # Server port
BUFFER_SIZE = 1024    # Packet size

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

# Read the BMP file 
with open("image.bmp", "rb") as f:
    file_data = f.read()

# Split file into packets
packets = [file_data[i:i+BUFFER_SIZE] for i in range(0, len(file_data), BUFFER_SIZE)]

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setting a timeout for ACK reception
client_socket.settimeout(1)

seq_num = 0
start_time = time.time()  # Start timing the transfer

# Log file header
write_log("Packet Log - Client Side")
write_log("Timestamp | Packet # | Action | Checksum | Status")

for packet in packets:
    checksum = check_sum(packet)

    # Pack [4-byte Sequence number] + [1-byte Checksum ] + [Data]
    header = struct.pack("I B", seq_num, checksum)
    full_packet = header + packet

    while True:
        # Send the packet
        client_socket.sendto(full_packet, (UDP_IP, UDP_PORT))
        print(f"Sent Packet {seq_num}")
        write_log(f"{time.time()} | {seq_num} | Sent | {checksum} | Success")

        try:
            ack_packet, _ = client_socket.recvfrom(4)  # Expect 4-byte ACK
            ack_num = struct.unpack("I", ack_packet)[0]  # Extract the ACK number

            # Simulate a % chance of ACK corruption
            if random.random() < 0.0:  # Probability of corruption
                ack_num ^= 1  # Flip the least significant bit (random error)
                print(f"Corrupted ACK received: {ack_num}, resending packet.")
                write_log(f"{time.time()} | {seq_num} | Resent | {checksum} | Corrupt ACK")
                continue

            if ack_num == seq_num:
                print(f"Received ACK {ack_num}, sending next packet.")
                seq_num = 1 - seq_num  # Flip the sequence number
                break  # Exit and move on to next packet
            else:
                write_log(f"{time.time()} | {seq_num} | Resent | {checksum} | Incorrect ACK")
                continue
        except socket.timeout:
            print(f"Ack not received for Packet {seq_num}, resending.")
            write_log(f"{time.time()} | {seq_num} | Lost | {checksum} | Timeout")

# Stop timing after last packet is successfully sent
end_time = time.time()
total_time = end_time - start_time

print("File transfer complete.")
print(f"Time taken to send corrupted file: {total_time:.2f} seconds.")  # Print total transmission time
write_log(f"File Transfer Completed in {total_time:.2f} seconds")

client_socket.sendto(b"STOP", (UDP_IP, UDP_PORT))
client_socket.close()