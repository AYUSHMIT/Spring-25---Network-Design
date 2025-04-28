import logger
logger.reset_log()
import threading
import time
import tcp_receiver
import tcp_sender


def start_receiver():
    """Start the TCP receiver (server)"""
    tcp_receiver.main()

def start_sender():
    """Start the TCP sender (client)"""
    time.sleep(1)  # small delay to ensure receiver is ready
    tcp_sender.main()

if __name__ == "__main__":
    # Create separate threads for receiver and sender
    receiver_thread = threading.Thread(target=start_receiver)
    sender_thread = threading.Thread(target=start_sender)

    # Start both threads
    receiver_thread.start()
    sender_thread.start()

    # Wait for both to complete
    receiver_thread.join()
    sender_thread.join()

    print("[Simulation]: Sender and Receiver completed.")
