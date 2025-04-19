import socket
import sys
from tcp_connection import SimpleTCPConnection
from network_simulator import NetworkSimulator
class TCPServer:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP socket
        self.connection = SimpleTCPConnection()  # Use custom TCP logic

    def start(self):
        try:
            self.sock.bind((self.server_ip, self.server_port))
            print(f"Server listening on {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"Failed to bind server socket: {e}")
            sys.exit(1)

    def handle_client(self):
        try:
            while True:
                data, addr = self.sock.recvfrom(1024)  # Receive data from client
                print(f"Received data from {addr}: {data.decode()}")

                # Process the received data using SimpleTCPConnection
                self.connection.handle_segment(data)

                # Example response
                response = "Hello, Client!"
                self.connection.send(response.encode())
                print(f"Sent response to {addr}: {response}")
        except KeyboardInterrupt:
            print("Server shutting down...")
        except Exception as e:
            print(f"Error handling client: {e}")

    def close(self):
        self.sock.close()
        print("Server socket closed.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    server = TCPServer(server_ip, server_port)
    server.start()
    server.handle_client()
    server.close()