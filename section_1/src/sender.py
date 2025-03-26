from utils import Timer, calculate_checksum, verify_checksum, introduce_bit_error, simulate_loss, make_packet, extract_sequence_number, extract_data
import socket
import struct
import time
import random
import os
import argparse
import matplotlib.pyplot as plt

# Constants
PACKET_SIZE = 1024
TIMEOUT = 0.05
MAX_WINDOW_SIZE = 50
ACK_SIGNAL = b'ACK'
DATA_LOSS_RATE = 0.2
ACK_LOSS_RATE = 0.2
BIT_ERROR_RATE = 0.1

def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFFFF
    return checksum

def make_packet(sequence_number, data, packet_type=b'DATA'):
    header_format = "!II4sH"
    header_size = struct.calcsize(header_format)

    if not isinstance(data, bytes):
        data = data.encode()

    checksum_data = packet_type + struct.pack("!II", sequence_number, len(data)) + data
    checksum = calculate_checksum(checksum_data)
    header = struct.pack(header_format, sequence_number, len(data), packet_type, checksum)
    return header + data + struct.pack("!H", checksum)

def simulate_loss(probability):
    return random.random() < probability

def introduce_bit_error(packet, error_probability):
    if random.random() < error_probability:
        index = random.randint(0, len(packet) - 1)
        bit_index = random.randint(0, 7)
        byte_array = bytearray(packet)
        byte_array[index] ^= (1 << bit_index)
        return bytes(byte_array)
    return packet

def rdt_rcv(sock, N, base):
    try:
        packet, _ = sock.recvfrom(PACKET_SIZE + 12)  # Adjust buffer size as needed
        if not packet:
            return None, None, None

        if not simulate_loss(ACK_LOSS_RATE):
            packet = introduce_bit_error(packet, BIT_ERROR_RATE)

        if not verify_checksum(packet):
            print("Checksum error, discarding packet")
            return None, None, None

        seq_num = extract_sequence_number(packet)
        if seq_num >= base and seq_num < base + N:
            return seq_num, extract_data(packet), packet
        else:
            return None, None, None
    except socket.timeout:
        return None, None, None

def rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer):
    if nextsegnum < base + N:
        print(f"Sending packet {nextsegnum}, base={base}, nextsegnum={nextsegnum}, N={N}")
        packet = make_packet(nextsegnum, data)
        sndpkt[nextsegnum % N] = packet
        if not simulate_loss(DATA_LOSS_RATE):
            print(f"Sending packet {nextsegnum} to {address}")
            sock.sendto(packet, address)
        else:
            print(f"Simulating loss of packet {nextsegnum}")

        if base == nextsegnum:
            timer.start(TIMEOUT)
        return nextsegnum + 1
    else:
        print("Refuse data, window is full")
        return nextsegnum

def run_go_back_n_sender(host, port, file_path, N):
    min_file_size = 500 * 1024  # 500KB in bytes
    file_size = os.path.getsize(file_path)
    if file_size < min_file_size:
        print(f"Error: Transfer file must be at least {min_file_size / 1024}KB. Current size: {file_size / 1024}KB")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    address = (host, port)
    timer = Timer()
    base = 0
    nextsegnum = 0
    sndpkt = [b''] * N

    try:
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(PACKET_SIZE)
                if not data:
                    break
                nextsegnum = rdt_send(sock, address, data, base, nextsegnum, N, sndpkt, timer)

                while base < nextsegnum:
                    if timer.is_expired():
                        print("Timeout, retransmitting packets")
                        timer.restart()
                        for i in range(base, nextsegnum):
                            if not simulate_loss(DATA_LOSS_RATE):
                                print(f"Retransmitting packet {i} to {address}")
                                sock.sendto(sndpkt[i % N], address)
                            else:
                                print(f"Simulating loss of packet {i}")
                    ack_num, _, _ = rdt_rcv(sock, N, base)
                    if ack_num is not None:
                        print(f"Received ACK {ack_num}")
                        base = ack_num + 1
                        if base == nextsegnum:
                            timer.stop()
                        else:
                            timer.restart()

                if base >= nextsegnum:
                    break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()

def run_experiment(host, port, file_path, window_size, loss_rate):
    global DATA_LOSS_RATE, ACK_LOSS_RATE, BIT_ERROR_RATE
    original_data_loss_rate = DATA_LOSS_RATE
    original_ack_loss_rate = ACK_LOSS_RATE
    original_bit_error_rate = BIT_ERROR_RATE

    DATA_LOSS_RATE = loss_rate
    ACK_LOSS_RATE = loss_rate
    BIT_ERROR_RATE = loss_rate

    start_time = time.time()
    run_go_back_n_sender(host, port, file_path, window_size)
    end_time = time.time()

    DATA_LOSS_RATE = original_data_loss_rate
    ACK_LOSS_RATE = original_ack_loss_rate
    BIT_ERROR_RATE = original_bit_error_rate

    return end_time - start_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Go-Back-N Sender for BMP files")
    parser.add_argument("file_path", help="Path to the BMP file to transfer")
    parser.add_argument("--host", default="localhost", help="Receiver host address")
    parser.add_argument("--port", type=int, default=12345, help="Receiver port number")
    parser.add_argument("--window_size", type=int, default=10, help="Go-Back-N window size")
    parser.add_argument("--enable_loss", action="store_true", help="Enable loss and error simulation")
    args = parser.parse_args()

    sender_host = args.host
    sender_port = args.port
    file_to_transfer = args.file_path
    window_size = args.window_size

    if not args.enable_loss:
        DATA_LOSS_RATE = 0.0
        ACK_LOSS_RATE = 0.0
        BIT_ERROR_RATE = 0.0

    # --- Performance Measurement for Chart 1 ---
    loss_probabilities = range(0, 75, 5)
    completion_times = []

    print("Running performance measurement for Chart 1...")
    for loss_prob in loss_probabilities:
        completion_time = run_experiment(sender_host, sender_port, file_to_transfer, window_size, loss_prob / 100.0)
        completion_times.append(completion_time)
        print(f"Loss Probability: {loss_prob}%, Completion Time: {completion_time:.2f} seconds")

    # Plotting Chart 1: Phase 4 performance
    plt.figure(figsize=(10, 6))
    plt.plot(loss_probabilities, completion_times, marker='o')
    plt.xlabel("Intentional loss probability (0% - 70%)")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Phase 4 Performance")
    plt.grid(True)
    plt.savefig("phase4_performance.png")
    print("Chart 1 saved as phase4_performance.png")

    # --- Performance Measurement for Chart 2 (Optimal Timeout) ---
    print("\nRunning performance measurement for Chart 2 (Optimal Timeout)...")
    timeout_values = range(10, 101, 10) # 10ms to 100ms
    timeout_completion_times = []
    fixed_loss_probability = 0.2 # 20% loss

    original_timeout = TIMEOUT
    for timeout_val in timeout_values:
        TIMEOUT = timeout_val / 1000.0 # Convert ms to seconds
        completion_time = run_experiment(sender_host, sender_port, file_to_transfer, window_size, fixed_loss_probability)
        timeout_completion_times.append(completion_time)
        print(f"Timeout Value: {timeout_val}ms, Completion Time: {completion_time:.2f} seconds")
    TIMEOUT = original_timeout # Restore original timeout

    plt.figure(figsize=(10, 6))
    plt.plot(timeout_values, timeout_completion_times, marker='o')
    plt.xlabel("Retransmission Timeout value (ms)")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Optimal Timeout Value - Phase 4 Performance (20% Loss)")
    plt.grid(True)
    plt.savefig("phase4_optimal_timeout.png")
    print("Chart 2 saved as phase4_optimal_timeout.png")

    # --- Performance Measurement for Chart 3 (Optimal Window Size) ---
    print("\nRunning performance measurement for Chart 3 (Optimal Window Size)...")
    window_sizes = [1, 2, 5, 10, 20, 30, 40, 50]
    window_completion_times = []
    fixed_loss_probability = 0.2 # 20% loss

    for win_size in window_sizes:
        completion_time = run_experiment(sender_host, sender_port, file_to_transfer, win_size, fixed_loss_probability)
        window_completion_times.append(completion_time)
        print(f"Window Size: {win_size}, Completion Time: {completion_time:.2f} seconds")

    plt.figure(figsize=(10, 6))
    plt.plot(window_sizes, window_completion_times, marker='o')
    plt.xlabel("Window Size")
    plt.ylabel("File Transfer Completion Time (seconds)")
    plt.title("Optimal Window Size - Phase 4 Performance (20% Loss)")
    plt.grid(True)
    plt.savefig("phase4_optimal_window_size.png")
    print("Chart 3 saved as phase4_optimal_window_size.png")

    print("\nRemember to implement the logic for Chart 4 (Performance comparison of different phases) separately.")

    # --- Performance Measurement for Chart 4 (Performance Comparison) ---
print("\nRunning performance measurement for Chart 4 (Performance Comparison)...")
fixed_loss_probability = 0.2  # 20% loss

# Replace these placeholders with actual measurements when implementing the respective phases
completion_time_phase2 = 0  # Replace with actual measurement for Phase 2
completion_time_phase3 = 0  # Replace with actual measurement for Phase 3
completion_time_phase4 = run_experiment(sender_host, sender_port, file_to_transfer, window_size, fixed_loss_probability)
completion_time_udp = 0  # Replace with actual measurement for UDP (if implemented)
completion_time_selective_repeat = 0  # Replace with actual measurement for Selective Repeat (if implemented)

phases = ['Phase 2', 'Phase 3', 'Phase 4']
times = [completion_time_phase2, completion_time_phase3, completion_time_phase4]

if completion_time_selective_repeat > 0:
    phases.append('Selective Repeat')
    times.append(completion_time_selective_repeat)
if completion_time_udp > 0:
    phases.append('UDP')
    times.append(completion_time_udp)

plt.figure(figsize=(10, 6))
plt.bar(phases, times, color='skyblue')
plt.xlabel("Phase")
plt.ylabel("File Transfer Completion Time (seconds)")
plt.title("Performance Comparison of Different Phases (20% Loss)")
plt.grid(axis='y')
plt.savefig("phase4_comparison.png")
print("Chart 4 saved as phase4_comparison.png")