import socket

# Server details
SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# File to transfer
filename = "image.bmp"

# Packet size
PACKET_SIZE = 1024

# Read the file data
with open(filename, "rb") as f:
    file_data = f.read()

# Calculate the number of packets
num_packets = len(file_data) // PACKET_SIZE + (1 if len(file_data) % PACKET_SIZE else 0)

# Convert num_packets to binary
binary_num_packets = format(num_packets, 'b')

# Send the binary number of packets to the server
print("Sending number of packets (binary):", binary_num_packets)
client_socket.sendto(binary_num_packets.encode(), (SERVER_IP, SERVER_PORT))

# Send the file data in packets
for i in range(num_packets):
    start = i * PACKET_SIZE
    end = min((i + 1) * PACKET_SIZE, len(file_data))
    packet = file_data[start:end]
    print("Sending packet:", i)
    client_socket.sendto(packet, (SERVER_IP, SERVER_PORT))

# Close the socket
client_socket.close()