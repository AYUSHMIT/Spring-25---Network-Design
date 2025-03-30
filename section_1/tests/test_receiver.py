import unittest
from src.receiver import run_go_back_n_receiver
from src.utils import make_packet
import socket
import os
import threading
import time

class TestReceiver(unittest.TestCase):
    def setUp(self):
        self.host = 'localhost'
        self.port = 54321
        self.output_file = r'C:\Users\ilary\OneDrive\Desktop\Spring-25---Network-Design\section_1\tests\received_image.bmp'
        self.test_image_path = r'C:\Users\ilary\OneDrive\Desktop\Spring-25---Network-Design\section_1\tests\test_image.bmp'
        
        # Create a dummy BMP file for testing
        with open(self.test_image_path, 'wb') as f:
            f.write(b'BM' + bytes(100) + b'\x00' * 100)

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
                print(f"{self.output_file} successfully deleted.")
            except PermissionError:
                print(f"Permission denied: Could not delete {self.output_file}.")
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_receiver_functionality(self):
        # Start the receiver in a separate thread
        receiver_thread = threading.Thread(target=run_go_back_n_receiver, args=(self.host, self.port, self.output_file))
        receiver_thread.start()
        
        # Allow the receiver to initialize
        time.sleep(0.5)
        
        # Simulate sending properly constructed packets to the receiver
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            seq = 0
            with open(self.test_image_path, 'rb') as f:
                chunk = f.read(1024)  # Read in chunks
                while chunk:
                    packet = make_packet(seq, chunk)
                    print(f"Sending packet with sequence {seq}, chunk size {len(chunk)}...")
                    sock.sendto(packet, (self.host, self.port))
                    seq += 1
                    chunk = f.read(1024)
            
            # Send a termination packet (e.g., with an empty payload and special packet type such as 'EOF ')
            eof_packet = make_packet(seq, b'', packet_type=b'EOF ')
            sock.sendto(eof_packet, (self.host, self.port))
        finally:
            sock.close()
        
        # Wait for the receiver to finish
        receiver_thread.join()

        # Check if the output file is created and verify its contents
        self.assertTrue(os.path.exists(self.output_file), "Output file was not created")
        self.assertGreater(os.path.getsize(self.output_file), 0, "Output file is empty")
        
        # Compare original and received files
        with open(self.test_image_path, 'rb') as f1, open(self.output_file, 'rb') as f2:
            self.assertEqual(f1.read(), f2.read(), "Output file content mismatch!")

if __name__ == '__main__':
    unittest.main()