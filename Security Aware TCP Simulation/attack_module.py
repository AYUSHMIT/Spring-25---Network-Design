import random
import time
from logger import log

# Attack probabilities (tweak as needed)
ACK_SPOOF_PROB = 0.1            # 10% chance to spoof ACK
DUP_ACK_FLOOD_PROB = 0.05       # 5% chance to flood duplicate ACKs
RTT_MANIPULATION_PROB = 0.2     # 20% chance to manipulate RTT

class AttackModule:
    def maybe_inject_attack(self, sock, seq_num):
        """Randomly decides whether to inject any attack during ACK sending"""
        
        # ACK Spoofing: send a fake ACK with incorrect sequence number
        if random.random() < ACK_SPOOF_PROB:
            spoof_seq = seq_num + random.randint(1, 5)
            try:
                sock.send(str(spoof_seq).encode())
                log(f"[ATTACK]: Spoofed ACK {spoof_seq} instead of {seq_num}")
            except Exception as e:
                log(f"[ATTACK ERROR]: {e}")

        # Duplicate ACK Flooding: flood 3 duplicate ACKs
        if random.random() < DUP_ACK_FLOOD_PROB:
            try:
                for _ in range(3):
                    sock.send(str(seq_num).encode())
                    log(f"[ATTACK]: Flooded Duplicate ACK {seq_num}")
                    time.sleep(0.01)  # tiny delay between duplicates
            except Exception as e:
                log(f"[ATTACK ERROR]: {e}")

        # RTT Manipulation: artificially delay before ACK
        if random.random() < RTT_MANIPULATION_PROB:
            delay = random.uniform(0.2, 0.5)  # delay between 200ms–500ms
            log(f"[ATTACK]: Artificial RTT delay of {int(delay * 1000)} ms")
            time.sleep(delay)
