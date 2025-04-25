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
        self.is_running = False


    def start(self):
        """Start the server, bind to the address, and set state to LISTEN."""
        try:
            self.sock.bind((self.server_ip, self.server_port))
            self.connection.state = 'LISTEN'  # Set state to LISTEN after successful bind
            print(f"Server listening on {self.server_ip}:{self.server_port}")
            # Ensure the server is ready to run
            self.is_running = True
        except socket.error as e:
            print(f"Error binding server socket: {e}")
            # Handle the error appropriately, e.g., exit or retry
            self.is_running = False  # Ensure the loop doesn't run if bind fails




    def receive_loop(self):
        """Continuously receive data from the server."""
        while self.is_running:  # Use the is_running flag to control the loop
            try:
                data, addr = self.sock.recvfrom(4096)
                self.connection.handle_segment(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"ERROR in receive_loop: {e}")
                break



    def close(self):
        self.is_running = False
        """Close the server socket."""
        self.sock.close()