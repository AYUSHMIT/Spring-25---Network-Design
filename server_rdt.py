import socket

# Server details
SERVER_PORT = 12345

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the specified port
server_socket.bind(('', SERVER_PORT))

print("Server listening on port", SERVER_PORT)

# Receive the binary number of packets from the client
binary_num_packets, client_address = server_socket.recvfrom(1024)
print("Received binary num_packets:", binary_num_packets)

# Convert binary to integer
num_packets = int(binary_num_packets.decode(), 2)
print("Number of packets:", num_packets)

# Receive the file data in packets
file_data = b""
for i in range(num_packets):
    packet, client_address = server_socket.recvfrom(1024)
    print("Received packet:", i)
    file_data += packet

# Save the received file data
with open("received_image.bmp", "wb") as f:
    f.write(file_data)

# Close the socket
server_socket.close()