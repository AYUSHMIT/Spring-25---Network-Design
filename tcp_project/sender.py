# sender.py

import socket
import struct
import time
import threading
import random
from tcp_segment import create_segment, parse_segment, compute_checksum
from utils import RTTManager, Timer
from congestion_control import CongestionControl
import logger

SERVER_IP = '127.0.0.1'
SERVER_PORT = 54321
ADDR = (SERVER_IP, SERVER_PORT)
MSS = 1000  # Max Segment Size
FILE_PATH = 'file_to_send.txt'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)

# TCP State Variables
seq_num = random.randint(0, 10000)
ack_num = 0
cwnd = 1  # Congestion window (segments)
ssthresh = 16  # Slow start threshold
rwnd = 50  # Assume receiver has large buffer
estimated_rtt = 0.5
dev_rtt = 0.25
timeout_interval = 1.0
rtt_manager = RTTManager()
cc = CongestionControl()
timer_dict = {}

# Connection Setup: 3-Way Handshake
def three_way_handshake():
    global ack_num
    print("[Sender] Starting 3-way handshake...")
    # Send SYN
    syn_segment = create_segment(seq_num, 0, syn=1, ack=0, fin=0, window=rwnd, payload=b'')
    sock.sendto(syn_segment, ADDR)
    logger.log(f"SYN sent (seq={seq_num})")

    # Receive SYN-ACK
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            segment = parse_segment(data)
            if segment['syn'] and segment['ack']:
                ack_num = segment['seq_num'] + 1
                logger.log(f"SYN-ACK received (ack={segment['ack_num']})")
                break
        except socket.timeout:
            sock.sendto(syn_segment, ADDR)

    # Send ACK
    ack_segment = create_segment(seq_num+1, ack_num, syn=0, ack=1, fin=0, window=rwnd, payload=b'')
    sock.sendto(ack_segment, ADDR)
    logger.log(f"ACK sent (seq={seq_num+1}, ack={ack_num})")

# Connection Teardown
def four_way_teardown():
    print("[Sender] Starting teardown...")
    fin_segment = create_segment(seq_num, ack_num, syn=0, ack=0, fin=1, window=rwnd, payload=b'')
    sock.sendto(fin_segment, ADDR)
    logger.log("FIN sent.")

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            segment = parse_segment(data)
            if segment['ack']:
                logger.log("ACK for FIN received.")
                break
        except socket.timeout:
            sock.sendto(fin_segment, ADDR)

# Sending Data
def send_file():
    global seq_num, ack_num, cwnd, ssthresh, timeout_interval

    with open(FILE_PATH, 'rb') as f:
        file_data = f.read()

    total_size = len(file_data)
    base = seq_num + 1
    next_seq = base
    data_ptr = 0
    acked = base

    start_time = time.time()

    while acked - base < total_size:
        while (next_seq - acked) < min(cwnd * MSS, rwnd * MSS) and data_ptr < total_size:
            payload = file_data[data_ptr:data_ptr+MSS]
            segment = create_segment(next_seq, 0, syn=0, ack=0, fin=0, window=rwnd, payload=payload)
            sock.sendto(segment, ADDR)
            timer_dict[next_seq] = Timer()
            timer_dict[next_seq].start()
            logger.log(f"Data segment sent (seq={next_seq})")
            next_seq += len(payload)
            data_ptr += len(payload)

        try:
            sock.settimeout(timeout_interval)
            data, addr = sock.recvfrom(4096)
            segment = parse_segment(data)
            if segment['ack']:
                ack_no = segment['ack_num']
                logger.log(f"ACK received (ack={ack_no})")
                if ack_no > acked:
                    sample_rtt = timer_dict.get(acked, None)
                    if sample_rtt:
                        sample_rtt = sample_rtt.stop()
                        rtt_manager.update(sample_rtt)
                        timeout_interval = rtt_manager.get_timeout()
                        logger.log_rtt(time.time() - start_time, sample_rtt)
                        logger.log_rto(time.time() - start_time, timeout_interval)
                    acked = ack_no
                    cc.on_ack()
                    cwnd = cc.cwnd
                    logger.log_cwnd(time.time() - start_time, cwnd)
        except socket.timeout:
            logger.log(f"Timeout occurred at seq={acked}")
            ssthresh = max(cwnd // 2, 1)
            cwnd = 1
            cc.on_timeout()
            timeout_interval *= 2
            segment = create_segment(acked, 0, syn=0, ack=0, fin=0, window=rwnd, payload=file_data[acked-base:acked-base+MSS])
            sock.sendto(segment, ADDR)
            timer_dict[acked] = Timer()
            timer_dict[acked].start()

    end_time = time.time()
    logger.log(f"File transfer completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    three_way_handshake()
    send_file()
    four_way_teardown()
    sock.close()
