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
        self.is_running = True
        """Start the server and bind to the specified address."""
        
        self.sock.bind((self.server_ip, self.server_port))
        print(f"Server listening on {self.server_ip}:{self.server_port}")

    def receive_loop(self):
        """Continuously receive data and process it."""
        try:
            self.sock.settimeout(1.0)  # Set timeout (e.g., 1 second)
            while self.is_running:  # Check the running flag
                try:
                    # Receive data from the simulator or directly from the socket
                    data, addr = self.simulator.recvfrom(self.sock, 1024) if self.simulator else self.sock.recvfrom(1024)
                    if data and not self.connection.remote_address:
                        # Learn the remote address if not already known
                        self.connection.remote_address = addr
                        print(f"DEBUG: Learned remote address: {addr}")
                    if data:
                        print(f"DEBUG: Server received data from {addr}")
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
        self.is_running = False
        """Close the server socket."""
        self.sock.close()