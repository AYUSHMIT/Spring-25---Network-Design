#!/usr/bin/env python3
"""
Author: Joseph Nguyen
Description: Receiver side implementation for sender-driven RDT 3.0 with error simulation.
The receiver:
  • Waits for a header packet and then for data packets.
  • Updates live progress in "progress.txt" and writes the received file ("received_file.jpg") incrementally.
  • Logs FSM events to "receiver_fsm.txt".
  • For Options 3, 4, 5, simulates errors as follows:
       Option 3: Simulate data packet bit-error (corrupt incoming data).
       Option 4: Simulate ACK loss (drop some ACKs).
       Option 5: Simulate data packet loss (drop some packets).
Usage:
    python server.py <save_filename> <mode> <loss_rate> <option>
    mode: "sender_driven"
Example:
    python server.py received_file.jpg sender_driven 10 3
"""

import socket, sys, struct, time, random, os

try:
    SIM_LOSS_RATE = float(sys.argv[3]) / 100.0
except Exception:
    SIM_LOSS_RATE = 0.0
try:
    option = int(sys.argv[4])
except Exception:
    option = 1

HEADER_SEQ = 0xFFFFFFFF

def compute_checksum(data):
    return sum(data) % 256

def parse_packet(packet):
    header_size = struct.calcsize("!I B I")
    header = packet[:header_size]
    seq, checksum, data_len = struct.unpack("!I B I", header)
    data = packet[header_size:header_size+data_len]
    return seq, checksum, data

def save_file(filename, packets):
    with open(filename, "wb") as f:
        for seq in sorted(packets.keys()):
            f.write(packets[seq])

def update_live_image(filename, packets):
    try:
        with open(filename, "wb") as f:
            for seq in sorted(packets.keys()):
                f.write(packets[seq])
    except Exception as e:
        print("Error updating live image:", e)

def update_progress_file(current, total):
    try:
        with open("progress.txt", "w") as f:
            f.write(f"{current} {total}")
    except Exception:
        pass

def log_receiver_fsm(message):
    try:
        with open("receiver_fsm.txt", "a") as f:
            # If message is bytes or contains bytes objects, convert to hex representation
            if isinstance(message, bytes):
                message = f"Binary data: {message.hex()}"
            f.write(f"[{time.time()}] {message}\n")
    except Exception:
        pass

def receive_file(save_filename, mode="sender_driven"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 20000))
    sock.settimeout(2)
    print("Receiver ready. Waiting for data...")
    received_packets = {}
    expected_seq = 0
    total_packets_value = None
    start_time = time.time()
    last_packet_time = time.time()

    while True:
        try:
            packet, addr = sock.recvfrom(2048)
            last_packet_time = time.time()
        except socket.timeout:
            if total_packets_value is not None and (time.time() - last_packet_time) > 10:
                break
            else:
                continue

        # Only treat the packet as a header if:
        #   - It starts with b"REQ "
        #   - It is short (e.g., <50 bytes)
        #   - The fifth byte is an ASCII digit (i.e. the header text is clean)
        if packet.startswith(b"REQ ") and len(packet) < 50 and (48 <= packet[4] <= 57):
            try:
                header_message = packet.decode("utf-8", errors="ignore").strip()
                # Expected format: "REQ <total_packets>"
                parts = header_message.split()
                if len(parts) != 2 or parts[0] != "REQ" or not parts[1].isdigit():
                    log_receiver_fsm("Header packet error: invalid header format")
                    # Not a valid header: fall through to binary processing
                else:
                    total_packets_value = int(parts[1])
                    print(f"Header received: total packets = {total_packets_value}")
                    log_receiver_fsm(f"Header received: total packets = {total_packets_value}")
                    update_progress_file(0, total_packets_value)
                    continue  # Skip further processing for header packet
            except Exception as e:
                log_receiver_fsm(f"Header packet decode error: {e}")
                continue

        # Otherwise, treat the packet as a binary data packet:
        try:
            seq, checksum, data = parse_packet(packet)
        except Exception as e:
            log_receiver_fsm(f"Error processing packet header: {e}")
            continue

        # For options 3 and 5, simulate errors at the receiver.
        if option == 3 and random.random() < SIM_LOSS_RATE:
            if len(data) > 0:
                index = random.randint(0, len(data)-1)
                corrupted_byte = data[index] ^ 0xFF
                data = data[:index] + bytes([corrupted_byte]) + data[index+1:]
        if option == 5 and random.random() < SIM_LOSS_RATE:
            log_receiver_fsm(f"Packet {seq} dropped (simulated data loss).")
            continue

        if compute_checksum(data) != checksum:
            log_receiver_fsm(f"Packet {seq} discarded (checksum error).")
            continue

        if seq == expected_seq:
            received_packets[seq] = data
            log_receiver_fsm(f"Packet {seq} received successfully.")
            expected_seq += 1
            if total_packets_value is not None:
                update_progress_file(expected_seq, total_packets_value)
            update_live_image("received_file.jpg", received_packets)

        # For option 4, simulate ACK loss.
        if option == 4 and random.random() < SIM_LOSS_RATE:
            log_receiver_fsm(f"ACK for packet {seq} dropped (simulated ACK loss).")
            continue

        ack_msg = f"ACK {seq}".encode()
        sock.sendto(ack_msg, addr)
    end_time = time.time()
    save_file(save_filename, received_packets)
    print("File received successfully.")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    log_receiver_fsm("File received successfully.")
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: server.py <save_filename> <mode> <loss_rate> <option>")
        sys.exit(1)
    save_filename = sys.argv[1]
    mode = sys.argv[2]
    try:
        sim_loss = float(sys.argv[3])
    except:
        sim_loss = 0.0
    try:
        option = int(sys.argv[4])
    except:
        option = 1
    receive_file(save_filename, mode)