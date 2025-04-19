class RTTEstimator:
    def __init__(self):
        self.rtt = None  # Estimated RTT
        self.dev = None  # Deviation in RTT

    def update(self, sample_rtt):
        """Updates the RTT estimator with a new SampleRTT."""
        if self.rtt is None:
            # Initialize RTT and deviation
            self.rtt = sample_rtt
            self.dev = sample_rtt / 2  # Initial deviation
        else:
            # Update RTT estimate using EWMA
            self.rtt = 0.875 * self.rtt + 0.125 * sample_rtt
            # Update deviation estimate using EWMA
            self.dev = 0.75 * self.dev + 0.25 * abs(sample_rtt - self.rtt)

    def get_timeout(self):
        """Calculates and returns the retransmission timeout (RTO)."""
        if self.rtt is not None and self.dev is not None:
            return self.rtt + 4 * self.dev
        return None