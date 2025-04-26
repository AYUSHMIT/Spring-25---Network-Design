import socket
import traceback
from tcp_connection import SimpleTCPConnection

class TCPServer:
    def __init__(self, server_ip, server_port, simulator=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.simulator = simulator
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable SO_REUSEADDR
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
        BUFFER_SIZE = 4096  # Define the buffer size for each recv() call

        while self.is_running:
            try:
                # Check if the socket is still valid before receiving
                if self.sock.fileno() == -1:  # Check if socket is closed
                    print("DEBUG: Server socket detected as closed, exiting receive loop.")
                    break

                # Use simulator if available
                data, addr = self.simulator.recvfrom(self.sock, BUFFER_SIZE) if self.simulator else self.sock.recvfrom(BUFFER_SIZE)

                if data:
                    print(f"DEBUG: Server received {len(data)} bytes from {addr}.")
                    # Process the received data
                    if hasattr(self.connection, 'handle_segment'):
                        self.connection.handle_segment(segment_bytes=data, client_address=addr)
                    else:
                        raise AttributeError("'SimpleTCPConnection' object missing 'handle_segment'")

            except socket.timeout:
                continue  # Optionally handle timeout without closing connection
            except OSError as e:
                if e.winerror == 10054:  # Connection reset by peer
                    print(f"WARNING: Connection reset by peer (expected in UDP). Continuing receive loop...")
                    continue  # <== KEY CHANGE: just continue instead of crashing
                elif e.winerror == 10038:  # WSAENOTSOCK (Socket operation on non-socket)
                    print("DEBUG: Socket not valid anymore, exiting.")
                    self.is_running = False
                    break
                elif e.winerror == 10022:  # WSAEINVAL (Invalid argument)
                    print("DEBUG: Invalid socket (10022), exiting.")
                    self.is_running = False
                    break
                else:
                    print(f"ERROR in receive_loop (OSError): {e}")
                    traceback.print_exc()
                    self.is_running = False
                    break
            except Exception as e:
                print(f"ERROR in receive_loop (Other Exception): {e}")
                traceback.print_exc()
                self.is_running = False
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