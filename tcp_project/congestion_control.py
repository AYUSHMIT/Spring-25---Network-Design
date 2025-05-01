# congestion_control.py

class CongestionControl:
    """Manages TCP congestion control (Slow Start, AIMD, Tahoe, Reno)."""
    def __init__(self, mode="reno"):
        self.cwnd = 1  # Start with 1 MSS
        self.ssthresh = 16
        self.mode = mode  # "reno" or "tahoe"

    def on_ack(self):
        if self.cwnd < self.ssthresh:
            # Slow start phase (exponential growth)
            self.cwnd *= 2
        else:
            # Congestion avoidance phase (linear growth)
            self.cwnd += 1

    def on_timeout(self):
        if self.mode == "reno" or self.mode == "tahoe":
            self.ssthresh = max(self.cwnd // 2, 1)
            self.cwnd = 1  # Reset to slow start
