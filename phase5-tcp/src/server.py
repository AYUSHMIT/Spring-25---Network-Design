import socket
from tcp_connection import SimpleTCPConnection

class TCPServer:
    def __init__(self, server_ip, server_port, simulator=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.simulator = simulator
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connection = SimpleTCPConnection()
        self.connection.sock = self.sock
        self.connection.simulator = self.simulator

    def start(self):
        """Start the server and bind to the specified address."""
        self.sock.bind((self.server_ip, self.server_port))
        print(f"Server listening on {self.server_ip}:{self.server_port}")

    def receive_loop(self):
        """Continuously receive data and process it."""
        try:
            while True:
                data, addr = self.simulator.recvfrom(self.sock, 1024) if self.simulator else self.sock.recvfrom(1024)
                if data and not self.connection.remote_address:
                    self.connection.remote_address = addr
                if data:
                    self.connection.handle_segment(data)
        except Exception as e:
            print(f"DEBUG: Error in receive loop: {e}")

    def close(self):
        """Close the server socket."""
        self.sock.close()