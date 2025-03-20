#!/usr/bin/env python3
"""
Receiver-Driven RDT 3.0 Receiver Implementation
------------------------------------------------
Role: Receiver
This script initiates data transfer by sending header and packet requests
to the sender. It writes progress updates to "progress.txt" and logs events
to "receiver_fsm.txt". The received file is saved to the specified filename.
------------------------------------------------
Usage:
    python3 server_rd.py <save_filename> <sender_ip> <loss_rate> <option>

Arguments:
    <save_filename> : File to save the received data.
    <sender_ip>     : IP address where the sender is running.
    <loss_rate>     : (Optional) Percentage for simulating packet loss or error.
    <option>        : (Optional) Simulation option.
"""

import socket, struct, sys, time, os, random

def compute_checksum(data):
    return sum(data) % 256

def parse_packet(packet):
    header_size = struct.calcsize("!I B I")
    header = packet[:header_size]
    seq, checksum, data_len = struct.unpack("!I B I", header)
    data = packet[header_size:header_size+data_len]
    return seq, checksum, data

def log_receiver_fsm(message):
    with open("receiver_fsm.txt", "a") as f:
        f.write(f"[{time.time()}] {message}\n")

def update_progress(current, total):
    with open("progress.txt", "w") as f:
        f.write(f"{current} {total}")

def receiver(save_filename, sender_addr, sim_loss=0.0, option=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 10000))
    sock.settimeout(2)
    
    expected_seq = 0
    received_packets = {}
    total_packets = None

    log_receiver_fsm("Receiver started, requesting header...")
    # Request header until received
    while total_packets is None:
        sock.sendto("REQ HEADER".encode(), sender_addr)
        try:
            msg, addr = sock.recvfrom(1024)
            msg_decoded = msg.decode().strip()
            if msg_decoded.startswith("HEADER"):
                parts = msg_decoded.split()
                if len(parts) == 2 and parts[1].isdigit():
                    total_packets = int(parts[1])
                    log_receiver_fsm(f"Received header: total packets = {total_packets}")
                    update_progress(0, total_packets)
        except socket.timeout:
            log_receiver_fsm("Header request timed out, retrying...")
            continue

    # Now request each packet in sequence
    while expected_seq < total_packets:
        req_msg = f"REQ {expected_seq}".encode()
        sock.sendto(req_msg, sender_addr)
        log_receiver_fsm(f"Requested packet {expected_seq}")
        try:
            packet, addr = sock.recvfrom(2048)
            if packet == b"END":
                log_receiver_fsm("Received END signal from sender.")
                break
            seq, checksum, data = parse_packet(packet)
            # Optionally simulate loss (e.g. option 5)
            if option == 5 and random.random() < sim_loss:
                log_receiver_fsm(f"Simulated loss for packet {seq}.")
                continue
            if compute_checksum(data) == checksum and seq == expected_seq:
                received_packets[seq] = data
                expected_seq += 1
                update_progress(expected_seq, total_packets)
                log_receiver_fsm(f"Received packet {seq} successfully.")
            else:
                log_receiver_fsm(f"Packet {expected_seq} failed checksum or sequence check, retrying.")
        except socket.timeout:
            log_receiver_fsm(f"Timeout waiting for packet {expected_seq}, re-requesting.")
            continue

    # Save the received file
    with open(save_filename, "wb") as f:
        for seq in sorted(received_packets.keys()):
            f.write(received_packets[seq])
    log_receiver_fsm("File transfer complete.")
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 server_rd.py <save_filename> <sender_ip> <loss_rate> <option>")
        sys.exit(1)
    save_filename = sys.argv[1]
    sender_ip = sys.argv[2]
    try:
        sim_loss = float(sys.argv[3]) / 100.0
    except Exception:
        sim_loss = 0.0
    try:
        option = int(sys.argv[4])
    except Exception:
        option = 1
    sender_port = 10001  # Sender listens on port 10001.
    sender_addr = (sender_ip, sender_port)
    receiver(save_filename, sender_addr, sim_loss, option)