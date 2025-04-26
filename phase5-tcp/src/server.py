import socket
import traceback
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
            self.is_running = True
        except socket.error as e:
            print(f"Error binding server socket: {e}")
            self.is_running = False  # Ensure the loop doesn't run if bind fails

    def receive_loop(self):
        """Continuously receive data from the server."""
        print("DEBUG: Server receive_loop starting.")
        while self.is_running:
            try:
                # Check if the socket is still valid before receiving
                if self.sock.fileno() == -1:  # Check if socket is closed
                    print("DEBUG: Server socket detected as closed, exiting receive loop.")
                    break

                # Use simulator if available
                data, addr = self.simulator.recvfrom(self.sock, 4096) if self.simulator else self.sock.recvfrom(4096)

                if data:
                    print(f"DEBUG: Server received data from {addr}")
                    # Diagnostic check
                    print(f"DEBUG: Checking attributes for self.connection (type: {type(self.connection)}):")
                    if hasattr(self.connection, 'handle_segment'):
                        print("DEBUG: Server found handle_segment method.")
                        self.connection.handle_segment(segment_bytes=data, client_address=addr)
                    else:
                        print("ERROR: Server COULD NOT FIND handle_segment method on self.connection.")
                        print(f"Available attributes: {dir(self.connection)}")
                        raise AttributeError("'SimpleTCPConnection' object has no attribute 'handle_segment'")

            except socket.timeout:
                continue
            except OSError as e:
                # Handle specific socket errors
                if e.winerror == 10038:  # WSAENOTSOCK (Socket operation on non-socket)
                    print(f"DEBUG: Server receive_loop caught OSError {e.winerror}: Socket was likely closed. Exiting loop.")
                elif e.winerror == 10022:  # WSAEINVAL (Invalid argument)
                    print(f"DEBUG: Server receive_loop caught OSError {e.winerror}: Invalid argument, possibly closed socket. Exiting loop.")
                else:
                    print(f"ERROR in receive_loop (OSError): {e}")
                    traceback.print_exc()
                self.is_running = False  # Stop the loop on socket errors
                break
            except Exception as e:
                print(f"ERROR in receive_loop (Other Exception): {e}")
                traceback.print_exc()
                self.is_running = False  # Stop the loop on other critical errors
                break
        print("DEBUG: Server receive_loop finished.")

    def close(self):
        """Close the server socket."""
        print("DEBUG: server.close() called.")
        self.is_running = False  # Ensure loop stops
        try:
            if self.sock:
                self.sock.close()
                print("DEBUG: Server socket closed.")
        except Exception as e:
            print(f"ERROR closing server socket: {e}")