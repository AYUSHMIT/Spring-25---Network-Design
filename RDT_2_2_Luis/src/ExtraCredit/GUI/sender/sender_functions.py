# Author: Luis D. Pena Mateo
# Description: Reliable Data Transfer (RDT) over a Perfectly Reliable Channel: RDT 1.0

#----------------------------------------
'''python libraries begins'''
#----------------------------------------
from socket import *  # Import socket library for network communication
from enum import Enum  # Import Enum class for defining states
import struct  # Import struct for working with binary data
import random  # Import random module to simulate data corruption (if applicable)
#----------------------------------------
'''End python libraries'''
#----------------------------------------

#########################################

#----------------------------------------
'''Constansts definitions begins'''
#----------------------------------------
PACKET_SIZE = 1024  # Packet size in bytes (maximum size of data in each packet)
FILE_PATH = "input_file.bmp"  # File path for the input file to be sent

# Sender details
HOST_A_PORT = 13000  # Port number to bind the sender's UDP socket

# Receiver details
HOST_B_ADDRESS = 'localhost'  # Receiver's address (localhost for local testing)
HOST_B_PORT = 12000  # Receiver's port number



class state(Enum):
    # Enum class to define sender's states in the state machine
    STATE_0 = "Current State: Wait from call 0 from above"  # Initial state, waiting for data
    STATE_1 = "Current State: Wait for ACK 0"  # Waiting for acknowledgment (ACK) for sequence 0
    STATE_2 = "Current State: Wait from call 1 from above"  # Waiting to send data for sequence 1
    STATE_3 = "Current State: Wait for ACK 1"  # Waiting for ACK for sequence 1

# State transition dictionary for handling state transitions
state_transitions = {
    state.STATE_0.name: {               # Define transitions for 'STATE_0'
        'NEXT': state.STATE_1.name,     # If input is 'NEXT', transition to 'STATE_1'
        'STAY': state.STATE_0.name      # If input is 'STAY', remain in 'STATE_0'
    },
    state.STATE_1.name: {               # Define transitions for 'STATE_1'
        'NEXT': state.STATE_2.name,     # If input is 'NEXT', transition to 'STATE_2'
        'STAY': state.STATE_1.name      # If input is 'STAY', remain in 'STATE_1'
    },
    state.STATE_2.name: {               # Define transitions for 'STATE_2'
        'NEXT': state.STATE_3.name,     # If input is 'NEXT', transition to 'STATE_3'
        'STAY': state.STATE_2.name      # If input is 'STAY', remain in 'STATE_2'
    },
    state.STATE_3.name: {               # Define transitions for 'STATE_3'
        'NEXT': state.STATE_0.name,     # If input is 'NEXT', transition to 'STATE_0'
        'STAY': state.STATE_3.name      # If input is 'STAY', remain in 'STATE_3'
    }
}

class PKT(Enum):
    CHECKSUM = 0
    SEQ_NUM  = 1
    DATA = 2
#----------------------------------------
''' End of Constants Definitions'''
#----------------------------------------

#########################################

#----------------------------------------
'''Global variables declaration begins'''
#----------------------------------------
# Create a UDP socket for sending data
senderSocket = socket(AF_INET, SOCK_DGRAM)  # Using IPv4 and UDP protocol
# Bind the socket to the local address and port
senderSocket.bind(('', HOST_A_PORT))
# Print a readiness message for the sender
print("The HOST_A is Ready to Transmit a file")
#----------------------------------------
'''End of Global variables declaration'''
#----------------------------------------

#########################################

#----------------------------------------
'''Function definition begins'''
#----------------------------------------

def get_user_choice():
    """
    Prompts the user for input (y/n) until valid input is provided.

    Returns:
    str: The validated user input ('y' or 'n').
    """
    try:
        answer = input("Send image, y/n?").strip().lower()  # Prompt user for input and normalize it
        if answer not in ['y', 'n']:
            # Raise error if input is invalid
            raise ValueError("Invalid input! Please enter 'y' or 'n'.")
        return answer  # Return valid input
    except ValueError as ve:
        print(ve)  # Print error message for invalid input

''' old
def get_file_data(file_path=FILE_PATH, packet_size=PACKET_SIZE):
    """
    Reads the input file and breaks it into packets of fixed size.

    Args:
    file_path (str): The path to the input file.
    packet_size (int): The size of each packet in bytes.

    Returns:
    list: A list containing file data divided into packets.
    """
    data = []
    try:
        with open(file_path, "rb") as f:  # Open the file in binary read mode
            file_data = f.read()  # Read the entire file
            for i in range(0, len(file_data), packet_size):
                # Divide the file data into chunks of size 'packet_size' and store in a list
                data.append(file_data[i:i + packet_size])
        return data  # Return the list of packets
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")  # Handle case where the file is missing
        return []
    except Exception as e:
        print(f"Error reading file: {e}")  # Handle other file reading exceptions
        return []
'''
#new
def get_file_data(file_path=FILE_PATH, packet_size=PACKET_SIZE):
    data = []
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            for i in range(0, len(file_data), packet_size):
                chunk = file_data[i:i + packet_size]
                if i + packet_size >= len(file_data):  # Final packet
                    chunk += b'EOF'  # Append "EOF" marker to the final packet
                data.append(chunk)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

def calculate_checksum(seq_num, data):
    """
    Computes the checksum using XOR operation.

    Args:
    seq_num (int): Sequence number of the packet.
    data (bytes): Data portion of the packet.

    Returns:
    int: The calculated checksum value.
    """
    checksum = seq_num  # Start with the sequence number
    for byte in data:
        # XOR the sequence number with each byte in the data
        checksum ^= byte
    return checksum  # Return the final checksum value

def make_pkt(seq_num, data, checksum):
    """
    Creates a packet containing sequence number, checksum, and data.

    Args:
    seq_num (int): Sequence number of the packet (0 or 1).
    data (bytes): Data portion of the packet.
    checksum (int): Calculated checksum for the packet.

    Returns:
    bytes: The complete packet consisting of the header and the data.
    """
    header = struct.pack("I B", checksum, seq_num)  # Pack checksum and sequence number into header
    return header + data  # Combine header with data to form the complete packet

def extract(packet):
    """
    Extracts header and data from a received packet.

    Args:
    packet (bytes): The received packet.

    Returns:
    tuple: A tuple containing checksum (int), sequence number (int), and data (bytes).
    """
    header_size = struct.calcsize("I B")  # Calculate size of the header (4 bytes for checksum, 1 byte for seq_num)
    checksum, seq_num = struct.unpack("I B", packet[:header_size])  # Unpack header
    data = packet[header_size:]  # Extract data portion of the packet
    return checksum, seq_num, data  # Return extracted components

def rdt_send(data, seq_num):
    """
    Sends a packet reliably using the sequence number and checksum.

    Args:
    data (bytes): The data portion of the packet to be sent.
    seq_num (int): The sequence number of the packet (0 or 1).
    """
    checksum = calculate_checksum(seq_num, data)  # Compute checksum for the data
    sndpkt = make_pkt(seq_num, data, checksum)  # Create a complete packet
    senderSocket.sendto(sndpkt, (HOST_B_ADDRESS, HOST_B_PORT))  # Send the packet via UDP to the receiver

def transition(state, input):
    """
    Handle state transitions based on the current state and input.

    Args:
        state (str): Current state name.
        input (str): Transition input ('NEXT' or 'STAY').

    Returns:
        str: Next state name.
    """
    return state_transitions[state].get(input, state)  # Get the next state or remain in the current state

#----------------------------------------
'''End of Function definition'''
#----------------------------------------