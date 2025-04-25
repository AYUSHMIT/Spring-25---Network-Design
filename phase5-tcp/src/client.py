import socket
from tcp_connection import SimpleTCPConnection

class TCPClient:
    def __init__(self, server_ip, server_port, simulator=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.simulator = simulator
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connection = SimpleTCPConnection()
        self.connection.sock = self.sock
        self.connection.simulator = self.simulator

    def connect(self):
        """Initiate a connection to the server."""
        remote_address = (self.server_ip, self.server_port)
        self.connection.connect(remote_address)

    def send_data(self, data):
        """Send application data."""
        print("DEBUG: Client attempting to send data.")
        self.connection.send(data)

    def receive_loop(self):
        """Continuously receive data and process it."""
        try:
            self.sock.settimeout(1.0)  # Set timeout (e.g., 1 second)
            while True:
                try:
                    # Receive data from the simulator or directly from the socket
                    data, addr = self.simulator.recvfrom(self.sock, 1024) if self.simulator else self.sock.recvfrom(1024)
                    if data:
                        print(f"DEBUG: Client received data from {addr}")

                        self.connection.handle_segment(data)
                except socket.timeout:
                    # No data received within timeout, just loop again
                    continue
                except Exception as e:
                    # Handle other potential recvfrom errors
                    print(f"DEBUG: Error in receive loop: {e}")
                    break  # Exit the loop on critical errors
        finally:
            # Ensure socket timeout is removed if needed elsewhere
            self.sock.settimeout(None)

    def close(self):
        """Close the connection."""
        self.connection.close()
        self.sock.close()