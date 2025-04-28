from tcp_sender import TCPSender
from tcp_receiver import TCPReceiver
from network_simulator import NetworkSimulator
from attack_module import AttackModule
from logger import setup_logger
import threading
import time

def main():
    logger = setup_logger()

    # Configure simulation parameters
    enable_attack = True
    attack_types = ["ack_spoofing", "duplicate_ack_flood", "rtt_manipulation"]

    # Setup simulator and components
    network = NetworkSimulator(attack_enabled=enable_attack)
    sender = TCPSender(network)
    receiver = TCPReceiver(network)
    attacker = AttackModule(network, attack_types)

    # Start threads
    sender_thread = threading.Thread(target=sender.start)
    receiver_thread = threading.Thread(target=receiver.start)
    if enable_attack:
        attack_thread = threading.Thread(target=attacker.start)
        attack_thread.start()

    sender_thread.start()
    receiver_thread.start()

    sender_thread.join()
    receiver_thread.join()
    if enable_attack:
        attacker.stop()

    logger.info("Simulation Completed.")

if __name__ == "__main__":
    main()
