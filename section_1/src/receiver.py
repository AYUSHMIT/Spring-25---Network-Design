import socket  # Provides socket communication
import struct  # Facilitates packing/unpacking binary data
import os  # Includes file handling and OS utilities
from .utils import calculate_checksum, verify_checksum, introduce_bit_error, simulate_loss, make_packet, extract_sequence_number, extract_data

# Constants for the program
PACKET_SIZE = 1024  # Size of data packets to be received
ACK_SIGNAL = b'ACK'  # Identifier for acknowledgment packets
DATA_LOSS_RATE = 0.2  # Probability of losing a data packet
ACK_LOSS_RATE = 0.2  # Probability of losing an acknowledgment packet
BIT_ERROR_RATE = 0.1  # Probability of introducing bit errors in packets

# Function to implement the Go-Back-N receiver
def run_go_back_n_receiver(host, port, output_file):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))  # Bind the socket to the specified host and port
    expectedsegnum = 0  # Tracks the next expected sequence number
    received_data = b''  # Buffer to store received data

    try:
        # Open the output file to write received data
        with open(output_file, 'wb') as file:
            while True:
                # Receive a packet (buffer size includes header and data)
                packet, address = sock.recvfrom(PACKET_SIZE + 12)
                if not packet:  # Exit loop if no packet is received
                    break

                # Simulate packet corruption by introducing bit errors
                if not simulate_loss(DATA_LOSS_RATE):
                    packet = introduce_bit_error(packet, BIT_ERROR_RATE)

                # Verify checksum to ensure data integrity
                if not verify_checksum(packet):
                    print("Checksum error, discarding packet")
                    # Send acknowledgment for the last correctly received packet
                    ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
                    sock.sendto(ack_packet, address)
                    continue

                # Extract sequence number from the received packet
                seq_num = extract_sequence_number(packet)

                # Handle in-order packets
                if seq_num == expectedsegnum:
                    print(f"Received expected packet {seq_num}")
                    data = extract_data(packet)  # Extract data from the packet
                    received_data += data  # Append data to buffer
                    file.write(data)  # Write data to output file

                    # Send acknowledgment for the received packet
                    ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
                    if not simulate_loss(ACK_LOSS_RATE):
                        sock.sendto(ack_packet, address)
                    expectedsegnum += 1  # Move to the next expected sequence number

                # Handle out-of-order packets
                else:
                    print(f"Out-of-order packet {seq_num}, expected {expectedsegnum}")
                    # Send acknowledgment for the last correctly received packet
                    ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
                    sock.sendto(ack_packet, address)

    except Exception as e:
        # Handle any exceptions that occur during execution
        print(f"Receiver: An error occurred: {e}")
    finally:
        # Ensure the socket is closed at the end
        sock.close()
    return len(received_data)  # Return the total number of bytes received

# Main function to run the receiver
if __name__ == "__main__":
    receiver_host = 'localhost'  # Receiver's IP address
    receiver_port = 5000  # Port on which the receiver listens
    output_file = 'received_image.bmp'  # Output file to save received data

    # Call the receiver function
    run_go_back_n_receiver(receiver_host, receiver_port, output_file)