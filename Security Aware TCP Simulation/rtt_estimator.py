import time

class RTTEstimator:
    def __init__(self):
        self.sample_start_time = None
        self.estimated_rtt = 0.5  # start with 500ms

    def update_rtt_sample(self):
        now = time.time()
        if self.sample_start_time:
            sample = now - self.sample_start_time
            self.estimated_rtt = 0.875 * self.estimated_rtt + 0.125 * sample
        self.sample_start_time = now

    def get_estimated_rtt(self):
        return self.estimated_rtt

