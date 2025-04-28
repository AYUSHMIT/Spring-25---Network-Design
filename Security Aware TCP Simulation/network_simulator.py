import random
import time
from logger import log

LOSS_RATE = 0.05  # 5% packet loss
DELAY_PROB = 0.3  # 30% chance to delay
MAX_DELAY = 0.2   # 200 ms

def simulate_network_conditions():
    if random.random() < LOSS_RATE:
        log("[Network]: Packet lost!")
        time.sleep(0.1)  # simulate loss effect
    if random.random() < DELAY_PROB:
        delay = random.uniform(0, MAX_DELAY)
        log(f"[Network]: Packet delayed by {int(delay*1000)}ms")
        time.sleep(delay)

