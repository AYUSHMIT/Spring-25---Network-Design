# receiver.py

import socket
import struct
import os
import random
from tcp_segment import create_segment, parse_segment, compute_checksum
import logger

SERVER_IP = '0.0.0.0'
SERVER_PORT = 54321
SAVE_PATH = 'received_file.txt'
MSS = 1000  # Max Segment Size

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

expected_seq = None
rwnd = 50  # Receiver window (in segments)

# Connection Setup: 3-Way Handshake
def three_way_handshake():
    global expected_seq
    print("[Receiver] Waiting for SYN...")

    while True:
        data, addr = sock.recvfrom(4096)
        segment = parse_segment(data)
        if segment['syn']:
            logger.log(f"Received SYN (seq={segment['seq_num']})")
            expected_seq = segment['seq_num'] + 1

            # Send SYN-ACK
            seq_num = random.randint(0, 10000)
            ack_num = expected_seq
            syn_ack_segment = create_segment(seq_num, ack_num, syn=1, ack=1, fin=0, window=rwnd, payload=b'')
            sock.sendto(syn_ack_segment, addr)
            logger.log(f"Sent SYN-ACK (seq={seq_num}, ack={ack_num})")
            break

    # Wait for final ACK
    while True:
        data, addr = sock.recvfrom(4096)
        segment = parse_segment(data)
        if segment['ack']:
            logger.log(f"Received ACK (ack={segment['ack_num']}) — Connection Established.")
            break

    return addr  # Return sender address to use later

# Data Receiving
def receive_file(addr):
    global expected_seq

    file_data = {}
    finished = False

    print("[Receiver] Receiving file data...")

    while not finished:
        try:
            data, _ = sock.recvfrom(4096)
            segment = parse_segment(data)

            if segment['fin']:
                logger.log("Received FIN. Sending ACK for FIN...")
                ack_segment = create_segment(expected_seq, segment['seq_num']+1, syn=0, ack=1, fin=0, window=rwnd, payload=b'')
                sock.sendto(ack_segment, addr)
                finished = True
                continue

            checksum_valid = compute_checksum(data) == 0
            if not checksum_valid:
                logger.log(f"Corrupted segment detected (seq={segment['seq_num']}). Dropping...")
                continue  # Drop corrupted packet

            seq_num = segment['seq_num']
            payload = segment['payload']

            if seq_num == expected_seq:
                file_data[seq_num] = payload
                expected_seq += len(payload)

                # Send ACK
                ack_segment = create_segment(expected_seq, 0, syn=0, ack=1, fin=0, window=rwnd, payload=b'')
                sock.sendto(ack_segment, addr)
                logger.log(f"ACK sent (ack={expected_seq})")
            else:
                # Duplicate ACK for last correct seq
                ack_segment = create_segment(expected_seq, 0, syn=0, ack=1, fin=0, window=rwnd, payload=b'')
                sock.sendto(ack_segment, addr)
                logger.log(f"Duplicate ACK sent (ack={expected_seq})")

        except socket.timeout:
            continue

    # Save received data
    with open(SAVE_PATH, 'wb') as f:
        sorted_seq = sorted(file_data.keys())
        for seq in sorted_seq:
            f.write(file_data[seq])

    print(f"[Receiver] File received and saved to '{SAVE_PATH}'.")

if __name__ == "__main__":
    sender_addr = three_way_handshake()
    receive_file(sender_addr)
    sock.close()
