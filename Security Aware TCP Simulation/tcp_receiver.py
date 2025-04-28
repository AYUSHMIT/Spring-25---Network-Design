import socket
import threading
import random
from network_simulator import simulate_network_conditions
from attack_module import AttackModule
from logger import log

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

attack_module = AttackModule()

def handle_client(client_sock):
    while True:
        pkt = client_sock.recv(1024)
        if not pkt:
            break
        seq_num = int(pkt.decode())
        log(f"[TCP]: Received packet {seq_num}")
        
        simulate_network_conditions()
        
        attack_module.maybe_inject_attack(client_sock, seq_num)
        
        client_sock.send(str(seq_num).encode())  # Normal ACK
        log(f"[TCP]: Sent ACK {seq_num}")

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen(1)
    print("Server listening...")

    client_sock, _ = server_sock.accept()
    handle_client(client_sock)

if __name__ == "__main__":
    main()
