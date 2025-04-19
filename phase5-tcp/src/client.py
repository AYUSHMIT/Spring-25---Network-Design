import socket
import sys
from tcp_connection import SimpleTCPConnection
from network_simulator import NetworkSimulator
class TCPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP socket
        self.connection = SimpleTCPConnection()  # Use custom TCP logic

    def connect(self):
        try:
            self.connection.connect((self.server_ip, self.server_port))
            print(f"Initiating connection to server at {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"Failed to initiate connection: {e}")
            sys.exit(1)

    def send_data(self, data):
        try:
            self.connection.send(data.encode())
            print("Data sent to server.")
        except Exception as e:
            print(f"Failed to send data: {e}")

    def receive_data(self):
        try:
            response = self.connection.receive()
            if response:
                print("Received data from server:", response.decode())
        except Exception as e:
            print(f"Failed to receive data: {e}")

    def close(self):
        self.connection.close()
        print("Connection closed.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    client = TCPClient(server_ip, server_port)
    client.connect()

    # Example of sending and receiving data
    client.send_data("Hello, Server!")
    client.receive_data()

    client.close()