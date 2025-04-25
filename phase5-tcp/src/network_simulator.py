import random
import time

class NetworkSimulator:
    def __init__(self, loss_rate=0.1, delay_rate=0.1, max_delay=0.5):
        """
        Simulates network conditions.
        :param loss_rate: Probability of dropping a packet (0.0 to 1.0).
        :param delay_rate: Probability of delaying a packet (0.0 to 1.0).
        :param max_delay: Maximum delay in seconds for delayed packets.
        """
        self.loss_rate = loss_rate
        self.delay_rate = delay_rate
        self.max_delay = max_delay

    def sendto(self, sock, data, addr):
        """
        Simulates sending data with packet loss and delay.
        :param sock: The UDP socket.
        :param data: The data to send.
        :param addr: The destination address.
        """
        if random.random() < self.loss_rate:
            print("[NetworkSimulator] Packet dropped.")
            return  # Simulate packet loss by not sending the packet

        if random.random() < self.delay_rate:
            delay = random.uniform(0, self.max_delay)
            print(f"[NetworkSimulator] Packet delayed by {delay:.2f} seconds.")
            time.sleep(delay)  # Simulate packet delay

        sock.sendto(data, addr)  # Send the packet
        print(f"[NetworkSimulator] Packet sent to {addr}")

        
    def recvfrom(self, sock, buffer_size):
        """Simulate receiving a packet."""
        if self.loss_rate > 0 and random.random() < self.loss_rate:
            print("DEBUG: Packet dropped due to loss rate.")
            return None, None  # Simulate packet loss
        if self.delay_rate > 0:
            delay = random.uniform(0, self.max_delay)
            print(f"DEBUG: Simulating network delay of {delay} seconds.")
            time.sleep(delay)
        return sock.recvfrom(buffer_size)