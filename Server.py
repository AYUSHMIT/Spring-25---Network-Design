# server.py
import socket

# Server details
server_port = 12345

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the specified port
server_socket.bind(('', server_port))

print("Server listening on port", server_port)

while True:
    # Receive the message from the client
    message, client_address = server_socket.recvfrom(1024)

    # Print the received message
    print("Received message:", message.decode(), "from", client_address)

    # Process the message (e.g., convert to uppercase)
    processed_message = message.decode().upper()

    # Send the processed message back to the client
    server_socket.sendto(processed_message.encode(), client_address)