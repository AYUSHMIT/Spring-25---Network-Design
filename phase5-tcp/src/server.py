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
        """Continuously receive data and process it."""
        try:
            self.sock.settimeout(1.0)  # Set timeout (e.g., 1 second)
            while self.is_running:
                try:
                    # Receive data from the simulator or directly from the socket
                    data, addr = self.simulator.recvfrom(self.sock, 1024) if self.simulator else self.sock.recvfrom(1024)
                    if data:
                        print(f"DEBUG: Server received data from {addr}")
                        self.connection.handle_segment(data, client_address=addr)  # Pass client address
                except socket.timeout:
                    # No data received within timeout, just loop again
                    continue
                except Exception as e:
                    print(f"DEBUG: Error in server receive loop: {e}")
                    break
        finally:
            self.sock.settimeout(None)



    def close(self):
        self.is_running = False
        """Close the server socket."""
        self.sock.close()