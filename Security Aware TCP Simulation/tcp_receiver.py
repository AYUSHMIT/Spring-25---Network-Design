import socket
import threading
from network_simulator import simulate_network_conditions
from attack_module import AttackModule
from logger import log

# Constants
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

attack_module = AttackModule()

def handle_client(client_sock):
    """Receiver logic to handle incoming packets and send ACKs"""
    while True:
        try:
            pkt = client_sock.recv(1024)
            if not pkt:
                break
            seq_num = int(pkt.decode())
            log(f"[TCP Receiver]: Received packet {seq_num}")

            # Simulate random network conditions (loss/delay)
            simulate_network_conditions()

            # Attack module may inject fake ACKs, dup ACKs, RTT manipulation
            attack_module.maybe_inject_attack(client_sock, seq_num)

            # Send normal ACK
            client_sock.send(str(seq_num).encode())
            log(f"[TCP Receiver]: Sent ACK {seq_num}")

        except Exception as e:
            log(f"[TCP Receiver ERROR]: {e}")
            break

def main():
    """Main function for the TCP Receiver (server)"""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen(1)
    log("[TCP Receiver]: Server listening...")

    client_sock, addr = server_sock.accept()
    log(f"[TCP Receiver]: Accepted connection from {addr}")

    handle_client(client_sock)

    client_sock.close()
    server_sock.close()
    log("[TCP Receiver]: Server closed.")

if __name__ == "__main__":
    main()
