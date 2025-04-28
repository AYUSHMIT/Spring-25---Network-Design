import socket
import threading
import time
from rtt_estimator import RTTEstimator
from logger import log

# Constants
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000
DATA_SIZE = 1000  # bytes per packet
TOTAL_PACKETS = 100  # total packets to send

# TCP State Variables
cwnd = 1          # congestion window size (packets)
ssthresh = 16     # slow start threshold
send_base = 0     # next expected ACK
lock = threading.Lock()

rtt_estimator = RTTEstimator()

def send_packets(sock):
    """Sender thread for sending packets"""
    global send_base, cwnd
    while send_base < TOTAL_PACKETS:
        lock.acquire()
        for i in range(send_base, min(send_base + cwnd, TOTAL_PACKETS)):
            data = f"{i}".encode()
            try:
                sock.send(data)
                log(f"[TCP Sender]: Sent packet {i}")
            except Exception as e:
                log(f"[TCP Sender ERROR]: {e}")
        lock.release()
        time.sleep(0.05)  # small interval between bursts

def receive_acks(sock):
    """Sender thread for receiving ACKs and adjusting cwnd"""
    global send_base, cwnd, ssthresh
    while send_base < TOTAL_PACKETS:
        try:
            ack = sock.recv(1024)
            if not ack:
                break
            ack_num = int(ack.decode())
            log(f"[TCP Sender]: Received ACK {ack_num}")
            rtt_estimator.update_rtt_sample()

            lock.acquire()
            if ack_num >= send_base:
                send_base = ack_num + 1
                if cwnd < ssthresh:
                    cwnd *= 2  # slow start phase
                else:
                    cwnd += 1  # congestion avoidance phase
            lock.release()

        except Exception as e:
            log(f"[TCP Sender ERROR]: {e}")
            break

def main():
    """Main function for the TCP Sender"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    log("[TCP Sender]: Connected to server.")

    send_thread = threading.Thread(target=send_packets, args=(sock,))
    ack_thread = threading.Thread(target=receive_acks, args=(sock,))

    send_thread.start()
    ack_thread.start()

    send_thread.join()
    ack_thread.join()

    sock.close()
    log("[TCP Sender]: Connection closed.")

if __name__ == "__main__":
    main()
