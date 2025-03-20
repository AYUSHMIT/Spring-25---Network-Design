#!/usr/bin/env python3
"""
Receiver-Driven RDT 3.0 Sender Implementation
------------------------------------------------
Role: Sender
This script reads the file to be transmitted, segments it into packets,
and then waits for requests from the receiver. When a request arrives,
it responds with the requested packet.
------------------------------------------------
Usage:
    python3 client_rd.py <filename> <receiver_ip> <loss_rate> <option>

Arguments:
    <filename>    : File to transmit.
    <receiver_ip> : IP address where the receiver is running.
    <loss_rate>   : (Optional) Percentage to simulate packet loss or error.
    <option>      : (Optional) Simulation option.
"""

import socket, sys, struct, time, random, os

# Optional simulation parameters
try:
    SIM_LOSS_RATE = float(sys.argv[3]) / 100.0
except Exception:
    SIM_LOSS_RATE = 0.0
try:
    option = int(sys.argv[4])
except Exception:
    option = 1

def compute_checksum(data):
    return sum(data) % 256

def make_packet(seq_num, data):
    checksum = compute_checksum(data)
    header = struct.pack("!I B I", seq_num, checksum, len(data))
    return header + data

def load_packets(filename, packet_size=1024):
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
    return packets

def sender(receiver_addr, filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set socket options to allow port reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        # SO_REUSEPORT might not be available on all systems.
        pass
    # Bind to a fixed port so that the receiver's requests reach us.
    sock.bind(('', 10001))
    sock.settimeout(2)
    
    packets = load_packets(filename)
    total_packets = len(packets)
    
    print(f"Loaded {total_packets} packets from {filename}.")
    
    # FSM for Sender:
    #   - If "REQ HEADER" is received, send header: "HEADER <total_packets>"
    #   - If "REQ <seq>" is received, send packet[seq]
    while True:
        try:
            message, addr = sock.recvfrom(1024)
            message = message.decode().strip()
            if message == "REQ HEADER":
                header_msg = f"HEADER {total_packets}".encode()
                sock.sendto(header_msg, addr)
                print("Sent header info to receiver.")
            elif message.startswith("REQ"):
                parts = message.split()
                if len(parts) != 2:
                    continue
                try:
                    req_seq = int(parts[1])
                except:
                    continue
                if req_seq < total_packets:
                    # (Optional: simulate packet loss/error for simulation option 2)
                    if option == 2 and random.random() < SIM_LOSS_RATE:
                        print(f"Simulating error for packet {req_seq} (not sending).")
                        continue
                    packet = packets[req_seq]
                    sock.sendto(packet, addr)
                    print(f"Sent packet {req_seq}")
                else:
                    # End-of-transmission: if requested sequence exceeds available packets
                    sock.sendto(b"END", addr)
                    print("Sent END signal.")
            else:
                print("Received unknown request:", message)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            break
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 client_rd.py <filename> <receiver_ip> <loss_rate> <option>")
        sys.exit(1)
    filename = sys.argv[1]
    receiver_ip = sys.argv[2]
    # Receiver listens on port 10000.
    receiver_port = 10000
    receiver_addr = (receiver_ip, receiver_port)
    sender(receiver_addr, filename)