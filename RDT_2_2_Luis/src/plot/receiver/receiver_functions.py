# Author: Luis D. Pena Mateo
# Description: Reliable Data Transfer (RDT) over a Perfectly Reliable Channel: RDT 1.0

#----------------------------------------
'''Python libraries begins'''
#----------------------------------------
from socket import *  # Import socket library for network communication
from enum import Enum  # Import Enum for defining states
import struct  # Import struct for working with binary data
#----------------------------------------
'''End python libraries'''
#----------------------------------------

#########################################

#----------------------------------------
'''Constants definitions begins'''
#----------------------------------------
PACKET_SIZE = 1024  # Define the size of each data packet in bytes

# Receiver details
HOST_B_PORT = 12000  # Define the port to which the receiver binds

class state(Enum):
    # Define states for the state machine
    STATE_0 = "Current State: Wait for 0 from below"  # Waiting for packets with sequence number 0
    STATE_1 = "Current State: Wait for 1 from below"  # Waiting for packets with sequence number 1

# State transition dictionary for handling state transitions
state_transitions = {
    state.STATE_0.name: {  # Transitions for STATE_0
        'NEXT': state.STATE_1.name,  # Transition to STATE_1
        'STAY': state.STATE_0.name   # Stay in STATE_0
    },
    state.STATE_1.name: {  # Transitions for STATE_1
        'NEXT': state.STATE_0.name,  # Transition to STATE_0
        'STAY': state.STATE_1.name   # Stay in STATE_1
    }
}

class PKT(Enum):
    CHECKSUM = 0
    SEQ_NUM  = 1
    DATA = 2
#----------------------------------------
'''End of Constants Definitions'''
#----------------------------------------

#########################################

#----------------------------------------
'''Global variables declaration begins'''
#----------------------------------------
# Create a UDP socket for communication
receiverSocket = socket(AF_INET, SOCK_DGRAM)  # Using IPv4 and UDP

# Bind the socket to the local address and specified port
receiverSocket.bind(('', HOST_B_PORT))
#----------------------------------------
'''End of Global variables declaration'''
#----------------------------------------

#########################################

#----------------------------------------
'''Function definitions begin'''
#----------------------------------------

def calculate_checksum(expected_seq_num, acknowledgement):
    """
    Calculate the checksum using XOR operation.
    
    Args:
        expected_seq_num (int): Expected sequence number (0 or 1).
        acknowledgement (bytes): Acknowledgment data.
    
    Returns:
        int: Computed checksum value.
    """
    checksum = expected_seq_num  # Initialize checksum with the sequence number
    for byte in acknowledgement:
        checksum ^= byte  # Perform XOR with each byte in the acknowledgment
    return checksum

def extract(packet):
    """
    Extract checksum, sequence number, and data from the packet.
    
    Args:
        packet (bytes): The received packet.
    
    Returns:
        tuple: Extracted checksum (int), sequence number (int), and data (bytes).
    """
    # Define header size: 4 bytes for checksum and 1 byte for sequence number
    header_size = struct.calcsize("I B")
    # Unpack checksum and sequence number from the header
    checksum, seq_num = struct.unpack("I B", packet[:header_size])
    # Extract the data part of the packet
    data = packet[header_size:]
    return checksum, seq_num, data

def deliver_data(data, number):
    """
    Deliver data to the application layer and save it to a file.
    
    Args:
        data (bytes): Received data payload.
        number (int): Output file sequence number for naming the file.
    """
    # Save received data to a file with a unique name based on the sequence number
    with open(f"Received_file{number}.bmp", "wb") as f:
        f.write(data)
    print("File received successfully and written to disk")  # Notify successful file saving

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

def make_pkt(expected_seq_num, Acknowledgement):
    """
    Create a packet with checksum, sequence number, and acknowledgment data.
    
    Args:
        expected_seq_num (int): Expected sequence number (0 or 1).
        Acknowledgement (bytes): Acknowledgment data.
    
    Returns:
        bytes: Constructed packet with checksum, sequence number, and acknowledgment.
    """
    # Calculate checksum for the acknowledgment
    checksum = calculate_checksum(expected_seq_num, Acknowledgement)
    # Create a packet header with checksum and sequence number
    header = struct.pack("I B", checksum, expected_seq_num)
    # Return the complete packet (header + acknowledgment data)
    return header + Acknowledgement

def is_final_packet(packet):
    """
    Detect if the packet is the final one by checking for the EOF marker in the data.

    Args:
        packet (bytes): The received packet.

    Returns:
        bool: True if EOF marker is found, False otherwise.
    """
    HEADER_SIZE = 5
    EOF_MARKER = b'EOF'
    data = packet[HEADER_SIZE:]  # Extract data portion
    return data.endswith(EOF_MARKER)  # Check for EOF marker


#----------------------------------------
'''End of Function definitions'''
#----------------------------------------