import threading
import time
import random
from common import Packet, send_buffer, ack_buffer, timer_table
from common import send_buffer_lock, ack_buffer_lock, timer_table_lock, cwnd, cwnd_lock, TIMEOUT, PACKET_GEN_INTERVAL

def sender_thread():
    """
    Simulates sending packets.
    Generates packets with sequence numbers and adds them to the send buffer.
    """
    seq_num = 0
    while seq_num < 50:  # Limit the number of packets to send
        packet = Packet(seq_num, f"Data_{seq_num}")  # Create a new packet
        
        with send_buffer_lock:
            send_buffer.append(packet)  # Add the packet to the send buffer
        
        with timer_table_lock:
            timer_table[seq_num] = time.time()  # Record the send time for the packet
        
        print(f"[SenderThread] Sent packet {seq_num}")
        seq_num += 1
        time.sleep(PACKET_GEN_INTERVAL)  # Simulate pacing between packet sends

def ack_receiver_thread():
    """
    Simulates receiving acknowledgments (ACKs) for sent packets.
    Randomly acknowledges packets from the send buffer.
    """
    while True:
        time.sleep(random.uniform(0.1, 0.3))  # Simulate random ACK delay
        with send_buffer_lock:
            if send_buffer:
                packet = random.choice(send_buffer)  # Randomly select a packet to acknowledge
                seq_num = packet.seq_num
                with ack_buffer_lock:
                    ack_buffer.append(seq_num)  # Add the sequence number to the ACK buffer
                with timer_table_lock:
                    timer_table.pop(seq_num, None)  # Remove the packet from the timer table
                send_buffer.remove(packet)  # Remove the packet from the send buffer
                print(f"[ACKReceiverThread] Received ACK for {seq_num}")

def timer_manager_thread():
    """
    Monitors the timer table for packet timeouts and retransmits packets if needed.
    """
    while True:
        time.sleep(0.1)  # Periodically check for timeouts
        now = time.time()
        with timer_table_lock:
            expired_packets = [seq_num for seq_num, send_time in timer_table.items() if now - send_time > TIMEOUT]
        for seq_num in expired_packets:
            with send_buffer_lock:
                for packet in send_buffer:
                    if packet.seq_num == seq_num:
                        print(f"[TimerManagerThread] Retransmitting packet {seq_num} due to timeout")
                        with timer_table_lock:
                            timer_table[seq_num] = time.time()  # Update the send time
                        break

def main():
    """
    Main function to start the sender, ACK receiver, and timer manager threads.
    """
    threading.Thread(target=sender_thread, daemon=True).start()
    threading.Thread(target=ack_receiver_thread, daemon=True).start()
    threading.Thread(target=timer_manager_thread, daemon=True).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()