import random
import time

class NetworkSimulator:
    def __init__(self, loss_rate=0.0, delay_rate=0.0, max_delay=0.0, burst_loss_rate=0.0, burst_length=3):
        """
        Simulates network conditions with optional packet loss, delay, and burst loss.
        :param loss_rate: Probability of dropping a packet (0.0 to 1.0).
        :param delay_rate: Probability of delaying a packet (0.0 to 1.0).
        :param max_delay: Maximum delay in seconds for delayed packets.
        :param burst_loss_rate: Probability of starting a burst loss (0.0 to 1.0).
        :param burst_length: Number of packets to drop in a burst.
        """
        self.loss_rate = loss_rate
        self.delay_rate = delay_rate
        self.max_delay = max_delay
        self.burst_loss_rate = burst_loss_rate  # Chance to start a burst
        self.burst_length = burst_length  # Number of packets to drop in a burst
        self.burst_counter = 0  # Countdown for ongoing burst

    def sendto(self, sock, packet, addr):
        """
        Simulates sending data with packet loss, delay, and burst loss.
        :param sock: The UDP socket.
        :param packet: The data to send.
        :param addr: The destination address.
        """
        # --- Handle burst loss ---
        if self.burst_counter > 0:
            self.burst_counter -= 1
            print("[NetworkSimulator] Burst packet dropped.")
            return  # Drop packet

        if random.random() < self.burst_loss_rate:
            self.burst_counter = self.burst_length - 1  # Start new burst
            print("[NetworkSimulator] Starting burst loss. Dropping packet.")
            return  # Drop first packet

        # --- Normal random loss ---
        if random.random() < self.loss_rate:
            print("[NetworkSimulator] Packet dropped.")
            return  # Drop packet

        # --- Random delay ---
        if random.random() < self.delay_rate:
            delay = random.uniform(0, self.max_delay)
            print(f"[NetworkSimulator] Packet delayed by {delay:.2f} seconds.")
            time.sleep(delay)

        # Actually send the packet
        sock.sendto(packet, addr)
        print(f"[NetworkSimulator] Packet sent to {addr}")

    def recvfrom(self, sock, buffer_size):
        """Simulate receiving a packet with optional loss/delay."""
        while True:
            # Always receive the packet first
            data, addr = sock.recvfrom(buffer_size)

            # Simulate packet loss
            if self.loss_rate > 0 and random.random() < self.loss_rate:
                print("DEBUG: Packet dropped after receiving due to loss simulation.")
                continue  # Discard this packet and wait for the next one

            # Simulate packet delay
            if self.delay_rate > 0:
                delay = random.uniform(0, self.max_delay)
                print(f"DEBUG: Simulating network delay of {delay:.2f} seconds.")
                time.sleep(delay)

            # Return the packet if not dropped
            return data, addr