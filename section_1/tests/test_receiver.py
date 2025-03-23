import unittest
from src.receiver import run_go_back_n_receiver
import socket
import os
import threading

class TestReceiver(unittest.TestCase):
    def setUp(self):
        self.host = 'localhost'
        self.port = 54321
        self.output_file = 'received_image.bmp'
        self.test_image_path = 'test_image.bmp'
        
        # Create a dummy BMP file for testing
        with open(self.test_image_path, 'wb') as f:
            f.write(b'BM' + bytes(100) + b'\x00' * 100)  # Simple BMP header + dummy data

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except PermissionError:
                pass
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_receiver_functionality(self):
        # Start the receiver in a separate thread
        receiver_thread = threading.Thread(target=run_go_back_n_receiver, args=(self.host, self.port, self.output_file))
        receiver_thread.start()
        
        # Simulate sending packets to the receiver (this part would be handled by the sender in a real scenario)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with open(self.test_image_path, 'rb') as f:
            data = f.read(1024)  # Read in chunks
            while data:
                sock.sendto(data, (self.host, self.port))
                data = f.read(1024)
        
        sock.close()
        receiver_thread.join()

        # Check if the output file is created and has the expected size
        self.assertTrue(os.path.exists(self.output_file))
        self.assertGreater(os.path.getsize(self.output_file), 0)

if __name__ == '__main__':
    unittest.main()