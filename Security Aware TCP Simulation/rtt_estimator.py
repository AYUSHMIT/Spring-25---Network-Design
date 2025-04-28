import time

class RTTEstimator:
    """Simple RTT estimator following TCP's Exponential Weighted Moving Average (EWMA)"""

    def __init__(self):
        self.sample_start_time = None
        self.estimated_rtt = 0.5  # Start with an assumed RTT of 500ms
        self.alpha = 0.125  # EWMA smoothing factor

    def start_sample(self):
        """Start measuring RTT"""
        self.sample_start_time = time.time()

    def update_rtt_sample(self):
        """Update RTT estimation based on the latest ACK"""
        now = time.time()
        if self.sample_start_time:
            sample_rtt = now - self.sample_start_time
            self.estimated_rtt = (1 - self.alpha) * self.estimated_rtt + self.alpha * sample_rtt
            self.sample_start_time = now  # Reset for next sample

    def get_estimated_rtt(self):
        """Returns current estimated RTT"""
        return self.estimated_rtt
