#!/usr/bin/env python3
"""
Author: Joseph Nguyen
Description: Sender-driven RDT 3.0 implementation with error simulation for five options.
Options:
  1 - Reliable channel (no error simulation)
  2 - Simulate ACK packet bit-error at the sender (corrupt received ACKs)
  3 - (Receiver simulates data packet bit-error)
  4 - (Receiver simulates ACK packet loss)
  5 - (Receiver simulates data packet loss)
Usage:
    python client.py <filename> <server_ip> <mode> <loss_rate> <option>
    mode must be "sender_driven"
Example:
    python client.py sample.jpg 127.0.0.1 sender_driven 10 2
"""

import socket, sys, struct, time, random, os, csv

# Configuration
INITIAL_PACKET_SIZE = 1024
MIN_PACKET_SIZE = 512
MAX_PACKET_SIZE = 1500
INITIAL_TIMEOUT = 0.05  # seconds
ALPHA = 0.125
BETA = 0.25

# Global counters (reset each transfer)
data_retransmissions = 0
ack_retransmissions = 0

HEADER_SEQ = 0xFFFFFFFF

# Get simulation loss rate and option from command-line
try:
    SIM_LOSS_RATE = float(sys.argv[4]) / 100.0
except Exception:
    SIM_LOSS_RATE = 0.0
try:
    option = int(sys.argv[5])
except Exception:
    option = 1

def compute_checksum(data):
    return sum(data) % 256

def make_packet(seq_num, data):
    checksum = compute_checksum(data)
    header = struct.pack("!I B I", seq_num, checksum, len(data))
    return header + data

def parse_ack(ack_packet):
    try:
        message = ack_packet.decode().strip()
        parts = message.split()
        if len(parts) == 2 and parts[0] == "ACK":
            return int(parts[1])
    except UnicodeDecodeError:
        # Not a text-based ACK packet
        return None
    except Exception:
        return None

def record_performance_data(option, loss_rate, completion_time, throughput, data_retx, ack_retx, ack_efficiency):
    with open("performance_data.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([option, loss_rate, completion_time, throughput, data_retx, ack_retx, ack_efficiency])

def update_stats_file(sent, acked, retrans):
    try:
        with open("stats.txt", "w") as f:
            f.write(f"sent:{sent} acked:{acked} retrans:{retrans}")
    except Exception:
        pass

def log_sender_fsm(message):
    try:
        with open("sender_fsm.txt", "a") as f:
            f.write(f"[{time.time()}] {message}\n")
    except Exception:
        pass

def send_file(filename, server_addr, mode="sender_driven", option=1):
    global data_retransmissions, ack_retransmissions
    start_time = time.time()
    
    # For Option 1, force simulation rate to 0.
    sim_rate = SIM_LOSS_RATE if option != 1 else 0.0

    estimated_rtt = INITIAL_TIMEOUT
    dev_rtt = INITIAL_TIMEOUT / 2
    current_timeout = INITIAL_TIMEOUT

    packet_size = INITIAL_PACKET_SIZE

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(current_timeout)

    if not os.path.isfile(filename):
        print("File not found!")
        sys.exit(1)
    with open(filename, "rb") as f:
        file_data = f.read()

    packets = []
    seq_num = 0
    for i in range(0, len(file_data), packet_size):
        chunk = file_data[i:i+packet_size]
        packets.append(make_packet(seq_num, chunk))
        seq_num += 1
    total_packets = len(packets)
    print(f"Total packets to send: {total_packets}")
    log_sender_fsm(f"Total packets to send: {total_packets}")

    # Send header packet as a text-based request
    header_packet = f"REQ {total_packets}".encode()
    sock.sendto(header_packet, server_addr)
    log_sender_fsm("Header packet sent.")
    time.sleep(0.1)

    base = 0
    while base < total_packets:
        packet = packets[base]
        send_time = time.time()
        sock.sendto(packet, server_addr)
        try:
            ack_packet, _ = sock.recvfrom(1024)
            # Option 2: Simulate ACK packet bit-error at sender.
            if option == 2 and random.random() < sim_rate:
                ack_packet = b"CORRUPT"
            ack_seq = parse_ack(ack_packet)
            rtt = time.time() - send_time
            if ack_seq is None or ack_seq != base:
                ack_retransmissions += 1
                log_sender_fsm(f"Packet {base}: ACK error. Retransmitting.")
                update_stats_file(base + data_retransmissions, base, data_retransmissions + ack_retransmissions)
                continue
            estimated_rtt = (1 - ALPHA) * estimated_rtt + ALPHA * rtt
            dev_rtt = (1 - BETA) * dev_rtt + BETA * abs(rtt - estimated_rtt)
            current_timeout = estimated_rtt + 4 * dev_rtt
            sock.settimeout(current_timeout)
            log_sender_fsm(f"Packet {base} ACK received. RTT: {rtt:.3f}s")
            base += 1
            update_stats_file(base + data_retransmissions, base, data_retransmissions + ack_retransmissions)
        except socket.timeout:
            data_retransmissions += 1
            current_timeout = min(0.2, current_timeout + 0.01)
            sock.settimeout(current_timeout)
            log_sender_fsm(f"Packet {base}: Timeout. Retransmitting.")
            update_stats_file(base + data_retransmissions, base, data_retransmissions + ack_retransmissions)

    completion_time = time.time() - start_time
    file_size = len(file_data)
    throughput = file_size / completion_time
    total_sent = base + data_retransmissions
    ack_efficiency = base / total_sent if total_sent > 0 else 0

    print("File transfer complete.")
    print(f"Completion time: {completion_time:.2f} seconds")
    print("Data retransmissions:", data_retransmissions)
    print("ACK retransmissions:", ack_retransmissions)
    print(f"Throughput: {throughput:.2f} bytes/s")
    log_sender_fsm(f"File transfer complete. Time: {completion_time:.2f}s, Data retrans: {data_retransmissions}, ACK retrans: {ack_retransmissions}")
    record_performance_data(option, int(sim_rate*100), completion_time, throughput,
                            data_retransmissions, ack_retransmissions, ack_efficiency)
    sock.close()
    return (completion_time, throughput, data_retransmissions, ack_retransmissions, ack_efficiency)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: client.py <filename> <server_ip> <mode> <loss_rate> <option>")
        sys.exit(1)
    filename = sys.argv[1]
    server_ip = sys.argv[2]
    mode = sys.argv[3]
    try:
        option_loss_rate = float(sys.argv[4])
    except:
        option_loss_rate = 0.0
    try:
        option = int(sys.argv[5])
    except:
        option = 1
    send_file(filename, (server_ip, 20000), mode, option)