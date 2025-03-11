import socket
import struct
import random
import time
import threading
from file_transfer import send_file, receive_file

class FileTransferServer:
    def __init__(self, address=('localhost', 12345)):
        self.address = address
        self.sock = self.create_udp_socket()
        self.listen_address = address
        self.save_path = 'received_image.jpg'

    def create_udp_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)  # Set a shorter timeout for socket operations
        return sock

    def start(self):
        threading.Thread(target=self.receive_file_with_status, daemon=True).start()

    def receive_file_with_status(self):
        try:
            print("Receiving file...")
            start_time = time.time()
            receive_file(self.update_fsm_state, option=1, error_rate=0.0, sock=self.sock, listen_address=self.listen_address, save_path=self.save_path)  # Pass the required arguments
            end_time = time.time()
            transfer_time = end_time - start_time
            print(f"File received successfully in {transfer_time:.2f} seconds!")
        except Exception as e:
            print(f"Error receiving file: {e}")

    def update_fsm_state(self, state):
        print(f"FSM State: {state}")

if __name__ == "__main__":
    server = FileTransferServer()
    server.start()
    while True:
        time.sleep(1)  # Keep the server running