import threading
import time
import random
from common import ack_buffer, ack_buffer_lock

def data_receiver_thread():
    """
    Simulates receiving data packets.
    Each packet is assigned a sequence number and added to the ACK buffer.
    """
    seq_num = 0  # Initialize sequence number
    while True:
        time.sleep(random.uniform(0.1, 0.3))  # Simulate random packet arrival
        print(f"[DataReceiverThread] Received packet {seq_num}")
        with ack_buffer_lock:  # Acquire lock to safely modify the ACK buffer
            ack_buffer.append(seq_num)  # Add the sequence number to the ACK buffer
        seq_num += 1  # Increment sequence number for the next packet

def ack_sender_thread():
    """
    Simulates sending acknowledgments (ACKs) for received packets.
    Continuously checks the ACK buffer and sends ACKs for sequence numbers.
    """
    while True:
        with ack_buffer_lock:  # Acquire lock to safely access the ACK buffer
            if ack_buffer:  # Check if there are ACKs to send
                seq_num = ack_buffer.pop(0)  # Remove the first sequence number from the buffer
                print(f"[ACKSenderThread] Sent ACK for {seq_num}")
        time.sleep(0.05)  # Simulate a delay between sending ACKs

def main():
    """
    Main function to start the receiver and sender threads.
    The program runs indefinitely, simulating a continuous flow of packets and ACKs.
    """
    threading.Thread(target=data_receiver_thread, daemon=True).start()
    threading.Thread(target=ack_sender_thread, daemon=True).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()