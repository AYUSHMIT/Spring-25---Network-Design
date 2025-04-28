import socket
import threading
import time
from rtt_estimator import RTTEstimator
from logger import log

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000
DATA_SIZE = 1000  # bytes
TOTAL_PACKETS = 100

cwnd = 1  # congestion window
ssthresh = 16
send_base = 0
lock = threading.Lock()

rtt_estimator = RTTEstimator()

def send_packets(sock):
    global send_base, cwnd
    while send_base < TOTAL_PACKETS:
        lock.acquire()
        for i in range(send_base, min(send_base + cwnd, TOTAL_PACKETS)):
            data = f"{i}".encode()
            sock.send(data)
            log(f"[TCP]: Sent packet {i}")
        lock.release()
        time.sleep(0.05)

def receive_acks(sock):
    global send_base, cwnd, ssthresh
    while send_base < TOTAL_PACKETS:
        ack = sock.recv(1024)
        if not ack:
            break
        ack_num = int(ack.decode())
        log(f"[TCP]: Received ACK {ack_num}")
        rtt_estimator.update_rtt_sample()
        lock.acquire()
        if ack_num >= send_base:
            send_base = ack_num + 1
            if cwnd < ssthresh:
                cwnd *= 2  # Slow Start
            else:
                cwnd += 1  # Congestion Avoidance
        lock.release()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    
    send_thread = threading.Thread(target=send_packets, args=(sock,))
    ack_thread = threading.Thread(target=receive_acks, args=(sock,))
    
    send_thread.start()
    ack_thread.start()
    
    send_thread.join()
    ack_thread.join()
    
    sock.close()

if __name__ == "__main__":
    main()

