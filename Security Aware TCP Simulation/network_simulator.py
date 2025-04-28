import random
import time
from logger import log

# Normal network behavior parameters
LOSS_RATE = 0.05       # 5% chance of packet loss
DELAY_PROB = 0.3       # 30% chance of random delay
MAX_DELAY = 0.2        # Maximum delay of 200ms

def simulate_network_conditions():
    """Simulate random network loss and delays to packets."""
    
    # Simulate packet loss
    if random.random() < LOSS_RATE:
        log("[Network Simulator]: Packet lost! (Simulated loss)")
        time.sleep(0.1)  # simulate packet loss by waiting
        return  # drop the packet (don't ACK back)

    # Simulate random packet delay
    if random.random() < DELAY_PROB:
        delay = random.uniform(0, MAX_DELAY)
        log(f"[Network Simulator]: Packet delayed by {int(delay * 1000)} ms")
        time.sleep(delay)
