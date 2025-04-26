import importlib
import socket
import tcp_connection
importlib.reload(tcp_connection)

from tcp_connection import SimpleTCPConnection
from tcp_segment import TCPSegment

conn = SimpleTCPConnection()

# Initialize the socket
conn.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
conn.remote_address = ("127.0.0.1", 54321)  # Set a valid remote address for testing

# Create a TCP segment
segment = TCPSegment(seq_num=0, ack_num=0, data=b'', flags=0x02)  # Example SYN segment

# Send the segment
conn._send_segment(segment)  # Test the method