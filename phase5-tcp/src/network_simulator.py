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

    def recvfrom(self, sock, buffer_size):
        """
        Simulates receiving data with packet loss and delay.
        :param sock: The UDP socket.
        :param buffer_size: The buffer size for receiving data.
        :return: The received data and address.
        """
        if random.random() < self.loss_rate:
            print("[NetworkSimulator] Incoming packet dropped.")
            time.sleep(random.uniform(0, self.max_delay))  # Simulate delay before dropping
            return None, None  # Simulate packet loss by returning nothing

        if random.random() < self.delay_rate:
            delay = random.uniform(0, self.max_delay)
            print(f"[NetworkSimulator] Incoming packet delayed by {delay:.2f} seconds.")
            time.sleep(delay)  # Simulate packet delay

        return sock.recvfrom(buffer_size)  # Receive the packet