import random  # For generating random numbers and simulating randomness
import time  # For tracking elapsed time and implementing timers
import struct  # For packing and unpacking binary data

# Function to simulate packet loss
def simulate_loss(probability):
    return random.random() < probability  # Returns True if a packet is lost (based on probability)

# Function to introduce bit errors into a packet
def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:  # Simulate error probability
        index = random.randint(0, len(packet) - 1)  # Select a random byte in the packet
        bit_index = random.randint(0, 7)  # Select a random bit in the byte
        byte_array = bytearray(packet)  # Convert packet to mutable bytearray
        byte_array[index] ^= (1 << bit_index)  # Flip the chosen bit in the byte
        return bytes(byte_array)  # Convert back to immutable bytes
    return packet  # Return the original packet if no error is introduced

# Function to read the contents of a BMP file
def read_bmp_file(file_path):
    with open(file_path, 'rb') as bmp_file:  # Open the file in binary read mode
        return bmp_file.read()  # Return the file contents as bytes

# Function to write data to a BMP file
def write_bmp_file(file_path, data):
    with open(file_path, 'wb') as bmp_file:  # Open the file in binary write mode
        bmp_file.write(data)  # Write the data (bytes) to the file

# Function to calculate a checksum for data integrity
def calculate_checksum(data): #1
    # Simple checksum: sum all byte values, limited to 16 bits
    checksum = 0
    for byte in data: # Iterate through each byte in the data
        checksum = (checksum + byte) & 0xFFFF # Add the byte value to the checksum & Limit the checksum to 16 bits
    return checksum


# Function to verify the checksum of a packet
def verify_checksum(packet):
    header_format = "!II4sH"  # Header format: sequence number, data length, packet type, checksum
    header_size = struct.calcsize(header_format)  # Compute header size
    header = packet[:header_size]  # Extract header
    seq, length, ptype, received_checksum = struct.unpack(header_format, header)
    
    # Slice exactly the number of data bytes specified by the header
    data = packet[header_size:header_size + length]
    
    # Recreate the checksum data exactly the same as in make_packet
    checksum_data = struct.pack("!II4s", seq, length, ptype) + data
    calculated_checksum = calculate_checksum(checksum_data)
    
    # For debugging, you might print:
    # print(f"Received: {received_checksum}, Calculated: {calculated_checksum}")
    return received_checksum == calculated_checksum

# Function to extract the sequence number from a packet
def extract_sequence_number(packet):
    header_format = "!II4sH"  # Header format
    header_size = struct.calcsize(header_format)  # Calculate header size
    header = packet[:header_size]  # Extract the header
    seq_num, _, _, _ = struct.unpack(header_format, header)  # Unpack the sequence number from the header
    return seq_num

# Function to extract the data from a packet
def extract_data(packet):
    header_format = "!II4sH"  # Header format
    header_size = struct.calcsize(header_format)  # Calculate header size
    # It is better to obtain the data length from the header to ensure correctness.
    _, data_length, _, _ = struct.unpack(header_format, packet[:header_size])
    return packet[header_size:header_size + data_length]

# Function to create a packet with a header, data, and checksum
def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"  # Header: sequence number, data length, packet type, checksum

    if not isinstance(data, bytes):
        data = data.encode()  # Ensure data is in bytes

    # Prepare the bytes used for checksum calculation (without including a slot for checksum)
    checksum_data = struct.pack("!II4s", sequence_number, len(data), packet_type) + data
    checksum = calculate_checksum(checksum_data)  # Calculate checksum
    
    # Pack the header including the computed checksum
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data  # Return the final packet

# Timer class for managing timeouts and intervals
class Timer:
    def __init__(self):
        self.start_time = None  # Tracks when the timer started
        self.interval = None  # Interval duration for the timer

    def start(self, interval):
        self.start_time = time.time()  # Record the current time as the start time
        self.interval = interval  # Set the interval duration

    def stop(self):
        self.start_time = None  # Clear the start time
        self.interval = None  # Clear the interval duration

    def is_expired(self):
        if self.start_time is None:  # Check if the timer is running
            return False
        return (time.time() - self.start_time) > self.interval  # Check if the interval has passed

    def restart(self):
        self.start(self.interval)  # Restart the timer with the same interval