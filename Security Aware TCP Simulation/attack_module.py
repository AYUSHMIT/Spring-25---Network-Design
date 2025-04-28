import random
import time
from logger import log

ACK_SPOOF_PROB = 0.1
DUP_ACK_FLOOD_PROB = 0.05
RTT_MANIPULATION_PROB = 0.2

class AttackModule:
    def maybe_inject_attack(self, sock, seq_num):
        if random.random() < ACK_SPOOF_PROB:
            spoof_seq = seq_num + random.randint(1, 5)
            sock.send(str(spoof_seq).encode())
            log(f"[ATTACK]: Spoofed ACK {spoof_seq}")

        if random.random() < DUP_ACK_FLOOD_PROB:
            for _ in range(3):
                sock.send(str(seq_num).encode())
                log(f"[ATTACK]: Flood duplicate ACK {seq_num}")

        if random.random() < RTT_MANIPULATION_PROB:
            delay = random.uniform(0.2, 0.5)
            log(f"[ATTACK]: Artificial RTT delay {int(delay*1000)}ms")
            time.sleep(delay)

