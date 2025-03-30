import socket
import struct
import time
import random

# Constants for configuration
PACKET_SIZE = 1024  # Maximum packet size in bytes
TIMEOUT = 0.05  # Timeout duration for retransmissions
MAX_WINDOW_SIZE = 50  # Maximum number of packets in the sliding window
ACK_SIGNAL = b'ACK'  # Signal used to represent acknowledgment packets
DATA_LOSS_RATE = 0.2  # Probability of data packet loss
ACK_LOSS_RATE = 0.2  # Probability of acknowledgment packet loss
BIT_ERROR_RATE = 0.1  # Probability of bit errors introduced in packets

# Helper functions for checksum calculation and verification
def calculate_checksum(data):
    # Computes a simple checksum by summing all bytes and masking to 16 bits
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFFFF
    return checksum

def verify_checksum(packet):
    header_format = "!II4sH"  # Header format: sequence number, data length, packet type, checksum
    header_size = struct.calcsize(header_format)  # Calculate the size of the header
    
    # Extract header and data
    header = packet[:header_size]  # Extract the header
    data = packet[header_size:]  # Extract the data (everything after the header)
    
    # Extract the checksum from the header
    unpacked_header = struct.unpack(header_format, header)  # Unpack the header into its components
    received_checksum = unpacked_header[-1]  # The last field is the checksum
    
    # Calculate the checksum for the header + data (excluding the received checksum)
    checksum_data = struct.pack("!II4s", unpacked_header[0], unpacked_header[1], unpacked_header[2]) + data
    calculated_checksum = calculate_checksum(checksum_data)
    
    # Return whether the received checksum matches the calculated checksum
    return received_checksum == calculated_checksum
'''
# Constructs a packet with a sequence number, data, and checksum
def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)

    if not isinstance(data, bytes):
        data = data.encode()  # Convert data to bytes if it is not already

    checksum_data = packet_type + struct.pack("!II", sequence_number, len(data)) + data
    checksum = calculate_checksum(checksum_data)
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data + struct.pack("!H", checksum)
'''

# Function to create a packet with a header, data, and checksum
def make_packet(sequence_number, data, packet_type=b'DATA'):
    # Header format: sequence number, data length, packet type, checksum
    header_format = "!II4sH"  # Header format for struct packing

    if not isinstance(data, bytes):  # Ensure the data is in bytes format
        data = data.encode()  # Convert string data to bytes

    # Prepare data for checksum calculation
    checksum_data = struct.pack("!II4s", sequence_number, len(data), packet_type) + data

    # Calculate the checksum for the packet
    checksum = calculate_checksum(checksum_data)

    # Pack the header and combine with data
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data  # Combine header and data into a packet

# Extracts various components from a packet
def extract_sequence_number(packet):
    return struct.unpack("!I", packet[:4])[0]

def extract_data(packet):
    # Header format matches the make_packet function
    header_format = "!II4sH"
    
    # Calculate the size of the header
    header_size = struct.calcsize(header_format)
    
    # Extract and return the data portion of the packet
    return packet[header_size:]

def extract_packet_type(packet):
    # Header format matches the make_packet function
    header_format = "!II4sH"
    
    # Extract and unpack the header to retrieve the packet type
    unpacked_header = struct.unpack(header_format, packet[:struct.calcsize(header_format)])
    packet_type = unpacked_header[2]  # The packet type is the third field in the header
    
    return packet_type

# Introduces a bit error to a packet with a given probability
def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)
        bit_index = random.randint(0, 7)
        byte_array = bytearray(packet)
        byte_array[index] ^= (1 << bit_index)  # Flip a random bit
        return bytes(byte_array)
    return packet

# Simulates packet loss with a given probability
def simulate_loss(probability):
    return random.random() < probability

# Timer class to track the timeout duration for retransmissions
class Timer:
    def __init__(self):
        self.start_time = 0
        self.running = False

    def start(self, duration):
        self.duration = duration
        self.start_time = time.time()
        self.running = True

    def stop(self):
        self.running = False
        self.start_time = 0

    def is_expired(self):
        if not self.running:
            return False
        return time.time() - self.start_time > self.duration

    def restart(self):
        self.start_time = time.time()
        self.running = True

# Implements the sender functionality for Go-Back-N ARQ protocol
def rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer):
    if nextsegnum < base + N:  # Check if window is not full
        print(f"rdt_send: Sending packet {nextsegnum}, base={base}, nextsegnum={nextsegnum}, N={N}")
        packet = make_packet(nextsegnum, data)
        sndpkt[nextsegnum % N] = packet
        if not simulate_loss(DATA_LOSS_RATE):
            sock.sendto(packet, address)
        else:
            print(f"rdt_send: Simulating loss of packet {nextsegnum}")

        if base == nextsegnum:  # Start timer if first unacknowledged packet
            timer.start(TIMEOUT)
        return nextsegnum + 1
    else:
        print("rdt_send: Refuse data, window is full")
        return nextsegnum

# Implements the receiver functionality for Go-Back-N ARQ protocol
def rdt_rcv(sock, N, expectedsegnum):
    try:
        packet, address = sock.recvfrom(4096)  # Receive packet
        if not packet:
            return None, None, expectedsegnum

    except socket.timeout:
        return None, None, expectedsegnum

    if not simulate_loss(DATA_LOSS_RATE):  # Introduce bit errors randomly
        packet = introduce_bit_error(packet, BIT_ERROR_RATE)

    if not verify_checksum(packet):  # Verify checksum
        print("rdt_rcv: Checksum error, discarding packet")
        ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
        sock.sendto(ack_packet, address)
        return None, address, expectedsegnum

    seq_num = extract_sequence_number(packet)
    packet_type = extract_packet_type(packet)

    if packet_type == ACK_SIGNAL:  # Handle acknowledgment packets
        return seq_num, address, expectedsegnum

    if seq_num == expectedsegnum:  # Correct and in-order packet
        print(f"rdt_rcv: Received expected packet {seq_num}")
        data = extract_data(packet)
        ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
        if not simulate_loss(ACK_LOSS_RATE):
            sock.sendto(ack_packet, address)
        else:
            print(f"rdt_rcv: Simulating loss of ACK for packet {expectedsegnum}")
        return data, address, expectedsegnum + 1
    else:  # Out-of-order packet
        print(f"rdt_rcv: Out-of-order packet {seq_num}, expected {expectedsegnum}")
        ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
        sock.sendto(ack_packet, address)
        return None, address, expectedsegnum

# Sender function for Go-Back-N protocol
def run_go_back_n_sender(host, port, file_path, N):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create UDP socket
    address = (host, port)
    timer = Timer()
    base = 0
    nextsegnum = 0
    sndpkt = [b''] * N
    file_size = 0

    try:
        with open(file_path, 'rb') as file:  # Read file to send
            while True:
                data = file.read(PACKET_SIZE)
                if not data:
                    break
                file_size += len(data)
                nextsegnum = rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer)

                # Handle retransmissions and acknowledgments
                while base < nextsegnum:
                    if timer.is_expired():
                        print("Sender: Timeout, retransmitting packets")
                        timer.restart()
                        for i in range(base, nextsegnum):
                            if not simulate_loss(DATA_LOSS_RATE):
                                sock.sendto(sndpkt[i % N], address)
                            else:
                                print(f"run_go_back_n_sender: Simulating loss of packet {i}")
                    ack_num, _, _ = rdt_rcv(sock, N, base)
                    if ack_num is not None:
                        print(f"Sender: Received ACK {ack_num}")
                        base = ack_num + 1
                        if base == nextsegnum:
                            timer.stop()
                        else:
                            timer.restart()

                if base >= nextsegnum:
                    break

    except Exception as e:
        print(f"Sender: An error occurred: {e}")
    finally:
        sock.close()
    return file_size

# Receiver function for Go-Back-N protocol
def run_go_back_n_receiver(host, port, output_file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create UDP socket
    sock.bind((host, port))
    expectedsegnum = 0
    received_data = b''

    try:
        with open(output_file, 'wb') as file:  # Write received data to file
            while True:
                data, _, expectedsegnum = rdt_rcv(sock, 1, expectedsegnum)
                if data:
                    received_data += data
                    file.write(data)
                    if len(received_data) % (1024 * 100) == 0:
                        print(f"Received {len(received_data)} bytes")
                elif data is None:
                    break

    except Exception as e:
        print(f"Receiver: An error occurred: {e}")
    finally:
        sock.close()
    return len(received_data)