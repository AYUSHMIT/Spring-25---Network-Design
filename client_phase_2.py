import socket
import struct
import random
from file_transfer import send_file
# Server details
SERVER_ADDRESS = ('localhost', 12351)  # Use the same port number as the server

# Packet size
PACKET_SIZE = 1024

def calculate_checksum(data):
    # Calculate the checksum using XOR
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum

def introduce_bit_error(data):
    # Introduce a bit error in the data
    if len(data) > 0:
        byte_index = random.randint(0, len(data) - 1)
        bit_index = random.randint(0, 7)
        data = bytearray(data)
        data[byte_index] ^= 1 << bit_index
    return bytes(data)

def send_file(file_path, update_fsm_state, option=1, error_rate=0.0):
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(10)  # Set a timeout for the socket

    # Read the file data
    with open(file_path, "rb") as f:
        file_data = f.read()

    # Calculate the number of packets
    num_packets = (len(file_data) + PACKET_SIZE - 1) // PACKET_SIZE

    # Send the number of packets to the server
    client_socket.sendto(struct.pack("!I", num_packets), SERVER_ADDRESS)
    update_fsm_state("Sent number of packets")
    print("Sent number of packets")

    # Send the file data in packets
    seq_num = 0
    for i in range(num_packets):
        start = i * PACKET_SIZE
        end = start + PACKET_SIZE
        packet_data = file_data[start:end]
        checksum = calculate_checksum(packet_data)
        packet = struct.pack("!II" + str(len(packet_data)) + "s", seq_num, checksum, packet_data)
        client_socket.sendto(packet, SERVER_ADDRESS)
        update_fsm_state(f"Sent packet {i} with sequence number {seq_num}")
        print(f"Sent packet {i} with sequence number {seq_num}")

        # Wait for ACK
        try:
            ack, _ = client_socket.recvfrom(2048)
            if len(ack) == 8:  # Ensure the ACK packet is 8 bytes long
                ack_seq_num, ack_checksum = struct.unpack("!II", ack)

                # Option 2: Introduce bit error in ACK packet for testing
                if option == 2 and random.random() < error_rate:
                    ack_seq_num = introduce_bit_error(struct.pack("!I", ack_seq_num))
                    ack_seq_num = struct.unpack("!I", ack_seq_num)[0]

                if ack_seq_num != seq_num:
                    print(f"Error: Incorrect ACK sequence number. Expected {seq_num}, got {ack_seq_num}")
                    continue  # Handle retransmission or other error recovery mechanisms
            else:
                print("Error: Received malformed ACK packet")
                continue  # Handle retransmission or other error recovery mechanisms
        except socket.timeout:
            print("Timeout waiting for ACK")
            continue  # Handle retransmission or other error recovery mechanisms
        except ConnectionResetError as e:
            print(f"ConnectionResetError: {e}")
            break

        seq_num = 1 - seq_num  # Toggle sequence number

    # Close the socket
    client_socket.close()
    update_fsm_state("File sent successfully")
    print("File sent successfully")

# Example usage
# filename = "phase_2.jpg"  # image file
# send_file(filename, update_fsm_state, option=1, error_rate=0.0)  # Option 1: No loss/bit-errors