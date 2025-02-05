# client.py
import socket

# Server details
server_ip = '127.0.0.1'
server_port = 12345

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # Get message from the user
    message = input("Enter message (or 'quit' to exit): ")
    if message == 'quit':
        break

    # Send the message to the server
    client_socket.sendto(message.encode(), (server_ip, server_port))

    # Receive the response from the server
    response, server_address = client_socket.recvfrom(1024)

    # Print the response
    print("Server response:", response.decode())

# Close the socket
client_socket.close()