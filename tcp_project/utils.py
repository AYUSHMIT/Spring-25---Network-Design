# utils.py

import time

class Timer:
    """Simple timer to measure segment RTT."""
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time is None:
            return None
        return time.time() - self.start_time

class RTTManager:
    """Manages RTT estimation and dynamic timeout calculation."""
    def __init__(self, alpha=0.125, beta=0.25):
        self.estimated_rtt = 1.0   # Initial guess
        self.dev_rtt = 0.5
        self.alpha = alpha
        self.beta = beta
        self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt

    def update(self, sample_rtt):
        self.estimated_rtt = (1 - self.alpha) * self.estimated_rtt + self.alpha * sample_rtt
        self.dev_rtt = (1 - self.beta) * self.dev_rtt + self.beta * abs(sample_rtt - self.estimated_rtt)
        self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt

    def get_timeout(self):
        return self.timeout_interval
