# Import required libraries
from .utils import Timer, calculate_checksum, verify_checksum, introduce_bit_error, simulate_loss, make_packet, extract_sequence_number, extract_data
import socket  # Used for network communication
import struct  # Helps with packing/unpacking binary data
import time  # Used for timing functionalities
import random  # Adds randomness for error/loss simulations
import os  # For file handling
import argparse  # For parsing command-line arguments
import matplotlib.pyplot as plt  # For visualizing results (not utilized in this snippet)

# Constants for configuration
PACKET_SIZE = 1024  # Maximum packet size in bytes
TIMEOUT = 0.05  # Timeout duration for retransmission
MAX_WINDOW_SIZE = 50  # Max number of packets in the sliding window
ACK_SIGNAL = b'ACK'  # Special identifier for acknowledgment packets
DATA_LOSS_RATE = 0.2  # Probability of losing a data packet
ACK_LOSS_RATE = 0.2  # Probability of losing an acknowledgment packet
BIT_ERROR_RATE = 0.1  # Probability of introducing bit errors into packets

# Helper function to calculate checksum of data
def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFFFF  # Keep checksum within 16-bit limit
    return checksum

# Helper function to construct a packet with header and data
def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"  # Header structure: seq num (int), length (int), type (4 bytes), checksum (short)
    header_size = struct.calcsize(header_format)  # Calculate header size

    if not isinstance(data, bytes):
        data = data.encode()  # Convert string data to bytes if needed

    # Prepare data for checksum calculation
    checksum_data = packet_type + struct.pack("!II", sequence_number, len(data)) + data
    checksum = calculate_checksum(checksum_data)

    # Pack header and data into a single packet
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data + struct.pack("!H", checksum)

# Simulate random loss of packets based on a given probability
def simulate_loss(probability):
    return random.random() < probability

# Simulate random bit errors in a packet based on a given probability
def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)  # Select a random byte in the packet
        bit_index = random.randint(0, 7)  # Select a random bit in the byte
        byte_array = bytearray(packet)  # Convert packet to mutable byte array
        byte_array[index] ^= (1 << bit_index)  # Flip the selected bit
        return bytes(byte_array)  # Convert back to immutable bytes
    return packet

# Function to receive packets and manage Go-Back-N protocol
def rdt_rcv(sock, N, base):
    try:
        # Receive a packet (buffer size includes header + data)
        packet, _ = sock.recvfrom(PACKET_SIZE + 12)
        if not packet:
            return None, None, None

        # Simulate random packet corruption
        if not simulate_loss(ACK_LOSS_RATE):
            packet = introduce_bit_error(packet, BIT_ERROR_RATE)

        # Verify checksum of the received packet
        if not verify_checksum(packet):
            print("Checksum error, discarding packet")
            return None, None, None

        # Extract sequence number and check if it's within the acceptable window
        seq_num = extract_sequence_number(packet)
        if base <= seq_num < base + N:
            return seq_num, extract_data(packet), packet  # Valid packet
        else:
            return None, None, None  # Invalid packet
    except socket.timeout:
        return None, None, None  # Handle socket timeout

# Function to send packets following the Go-Back-N protocol
def rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer):
    if nextsegnum < base + N:  # Ensure window is not full
        print(f"Sending packet {nextsegnum}, base={base}, nextsegnum={nextsegnum}, N={N}")
        packet = make_packet(nextsegnum, data)  # Create the packet
        sndpkt[nextsegnum % N] = packet  # Store the packet for potential retransmission

        if not simulate_loss(DATA_LOSS_RATE):  # Send the packet if not lost
            print(f"Sending packet {nextsegnum} to {address}")
            sock.sendto(packet, address)
        else:
            print(f"Simulating loss of packet {nextsegnum}")

        if base == nextsegnum:  # Start timer for the first unacknowledged packet
            timer.start(TIMEOUT)
        return nextsegnum + 1
    else:
        print("Refuse data, window is full")
        return nextsegnum  # Window is full, cannot send more packets

# Main function to implement the Go-Back-N sender
def run_go_back_n_sender(host, port, file_path, N):
    min_file_size = 500 * 1024  # Minimum file size in bytes (500 KB)
    file_size = os.path.getsize(file_path)
    if file_size < min_file_size:
        print(f"Error: Transfer file must be at least {min_file_size / 1024}KB. Current size: {file_size / 1024}KB")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
    address = (host, port)  # Define sender's address
    timer = Timer()
    base = 0  # First unacknowledged packet
    nextsegnum = 0  # Next packet to send
    sndpkt = [b''] * N  # Buffer for storing packets

    try:
        # Open file to read data
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(PACKET_SIZE)  # Read a chunk of data
                if not data:  # End of file
                    break
                nextsegnum = rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer)

                # Wait for acknowledgments and handle retransmissions
                while base < nextsegnum:
                    if timer.is_expired():  # Timer expired, retransmit packets
                        print("Timeout, retransmitting packets")
                        timer.restart()
                        for i in range(base, nextsegnum):
                            if not simulate_loss(DATA_LOSS_RATE):
                                print(f"Retransmitting packet {i} to {address}")
                                sock.sendto(sndpkt[i % N], address)
                            else:
                                print(f"Simulating loss of packet {i}")
                    ack_num, _, _ = rdt_rcv(sock, N, base)  # Wait for ACK
                    if ack_num is not None:
                        print(f"Received ACK {ack_num}")
                        base = ack_num + 1  # Slide window
                        if base == nextsegnum:
                            timer.stop()  # Stop timer when all packets are acknowledged
                        else:
                            timer.restart()  # Restart timer for remaining packets

                if base >= nextsegnum:  # All packets in the window are acknowledged
                    break

    except Exception as e:
        print(f"An error occurred: {e}")  # Handle exceptions gracefully
    finally:
        sock.close()  # Ensure socket is closed after use

def run_experiment(host, port, file_path, window_size, loss_rate):
    # Save the original values of global variables
    global DATA_LOSS_RATE, ACK_LOSS_RATE, BIT_ERROR_RATE
    original_data_loss_rate = DATA_LOSS_RATE
    original_ack_loss_rate = ACK_LOSS_RATE
    original_bit_error_rate = BIT_ERROR_RATE

    # Update loss and error rates for the experiment
    DATA_LOSS_RATE = loss_rate
    ACK_LOSS_RATE = loss_rate
    BIT_ERROR_RATE = loss_rate

    # Measure the time taken for file transfer
    start_time = time.time()
    run_go_back_n_sender(host, port, file_path, window_size)  # Send the file using Go-Back-N protocol
    end_time = time.time()

    # Restore the original loss and error rates
    DATA_LOSS_RATE = original_data_loss_rate
    ACK_LOSS_RATE = original_ack_loss_rate
    BIT_ERROR_RATE = original_bit_error_rate

    # Return the total duration of the experiment
    return end_time - start_time


if __name__ == "__main__":
    # Argument parser for user input
    parser = argparse.ArgumentParser(description="Go-Back-N Sender for BMP files")
    parser.add_argument("file_path", help="Path to the BMP file to transfer")  # File to be transferred
    parser.add_argument("--host", default="localhost", help="Receiver host address")  # Host IP
    parser.add_argument("--port", type=int, default=12345, help="Receiver port number")  # Host port
    parser.add_argument("--window_size", type=int, default=10, help="Go-Back-N window size")  # Sliding window size
    parser.add_argument("--enable_loss", action="store_true", help="Enable loss and error simulation")  # Enable/disable loss
    args = parser.parse_args()

    # Parse arguments provided by the user
    sender_host = args.host
    sender_port = args.port
    file_to_transfer = args.file_path
    window_size = args.window_size

    # Disable loss/error simulations if not explicitly enabled
    if not args.enable_loss:
        DATA_LOSS_RATE = 0.0
        ACK_LOSS_RATE = 0.0
        BIT_ERROR_RATE = 0.0

    # --- Chart 1: Performance vs Loss Rate ---
    loss_probabilities = range(0, 75, 5)  # Loss probabilities from 0% to 70% in steps of 5%
    completion_times = []  # Store completion times for each loss rate

    print("Running performance measurement for Chart 1...")
    for loss_prob in loss_probabilities:
        # Run experiment with varying loss probabilities
        completion_time = run_experiment(sender_host, sender_port, file_to_transfer, window_size, loss_prob / 100.0)
        completion_times.append(completion_time)
        print(f"Loss Probability: {loss_prob}%, Completion Time: {completion_time:.2f} seconds")

    # Plot the results for Chart 1
    plt.figure(figsize=(10, 6))
    plt.plot(loss_probabilities, completion_times, marker='o')
    plt.xlabel("Intentional loss probability (0% - 70%)")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Phase 4 Performance")
    plt.grid(True)
    plt.savefig("phase4_performance.png")
    print("Chart 1 saved as phase4_performance.png")

    # --- Chart 2: Performance vs Timeout Value ---
    print("\nRunning performance measurement for Chart 2 (Optimal Timeout)...")
    timeout_values = range(10, 101, 10)  # Timeout values from 10ms to 100ms
    timeout_completion_times = []  # Store completion times for each timeout value
    fixed_loss_probability = 0.2  # Fixed loss probability (20%)

    original_timeout = TIMEOUT  # Save original timeout value
    for timeout_val in timeout_values:
        TIMEOUT = timeout_val / 1000.0  # Convert timeout value from milliseconds to seconds
        completion_time = run_experiment(sender_host, sender_port, file_to_transfer, window_size, fixed_loss_probability)
        timeout_completion_times.append(completion_time)
        print(f"Timeout Value: {timeout_val}ms, Completion Time: {completion_time:.2f} seconds")
    TIMEOUT = original_timeout  # Restore original timeout value

    # Plot the results for Chart 2
    plt.figure(figsize=(10, 6))
    plt.plot(timeout_values, timeout_completion_times, marker='o')
    plt.xlabel("Retransmission Timeout value (ms)")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Optimal Timeout Value - Phase 4 Performance (20% Loss)")
    plt.grid(True)
    plt.savefig("phase4_optimal_timeout.png")
    print("Chart 2 saved as phase4_optimal_timeout.png")

    # --- Chart 3: Performance vs Window Size ---
    print("\nRunning performance measurement for Chart 3 (Optimal Window Size)...")
    window_sizes = [1, 2, 5, 10, 20, 30, 40, 50]  # Different window sizes
    window_completion_times = []  # Store completion times for each window size
    fixed_loss_probability = 0.2  # Fixed loss probability (20%)

    for win_size in window_sizes:
        # Run experiment for each window size
        completion_time = run_experiment(sender_host, sender_port, file_to_transfer, win_size, fixed_loss_probability)
        window_completion_times.append(completion_time)
        print(f"Window Size: {win_size}, Completion Time: {completion_time:.2f} seconds")

    # Plot the results for Chart 3
    plt.figure(figsize=(10, 6))
    plt.plot(window_sizes, window_completion_times, marker='o')
    plt.xlabel("Window Size")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Optimal Window Size - Phase 4 Performance (20% Loss)")
    plt.grid(True)
    plt.savefig("phase4_optimal_window_size.png")
    print("Chart 3 saved as phase4_optimal_window_size.png")

    print("\nRemember to implement the logic for Chart 4 (Performance comparison of different phases) separately.")

    # --- Chart 4: Performance Comparison ---
    print("\nRunning performance measurement for Chart 4 (Performance Comparison)...")
    fixed_loss_probability = 0.2  # Fixed loss probability (20%)

    # Placeholder values for other phases and techniques
    completion_time_phase2 = 0  # Replace with actual measurement for Phase 2
    completion_time_phase3 = 0  # Replace with actual measurement for Phase 3
    completion_time_phase4 = run_experiment(sender_host, sender_port, file_to_transfer, window_size, fixed_loss_probability)
    completion_time_udp = 0  # Replace with actual measurement for UDP (if implemented)
    completion_time_selective_repeat = 0  # Replace with actual measurement for Selective Repeat (if implemented)

    # Phases and completion times for comparison
    phases = ['Phase 2', 'Phase 3', 'Phase 4']
    times = [completion_time_phase2, completion_time_phase3, completion_time_phase4]

    # Append additional techniques if available
    if completion_time_selective_repeat > 0:
        phases.append('Selective Repeat')
        times.append(completion_time_selective_repeat)
    if completion_time_udp > 0:
        phases.append('UDP')
        times.append(completion_time_udp)

    # Plot the results for Chart 4
    plt.figure(figsize=(10, 6))
    plt.bar(phases, times, color='skyblue')
    plt.xlabel("Phase")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Performance Comparison of Different Phases (20% Loss)")
    plt.grid(axis='y')
    plt.savefig("phase4_comparison.png")
    print("Chart 4 saved as phase4_comparison.png")