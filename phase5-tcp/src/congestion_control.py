class CCState:
    WAITING = "waiting"
    SLOW_START = "slow_start"
    CONGESTION_AVOIDANCE = "congestion_avoidance"
    FAST_RECOVERY = "fast_recovery"

class CongestionControl:
    def __init__(self):
        self.state = CCState.WAITING
        self.congestion_window = 1  # Initial congestion window size
        self.ssthresh = 64  # Slow start threshold

    def on_packet_ack(self):
        if self.state == CCState.SLOW_START:
            self.congestion_window += 1
            if self.congestion_window >= self.ssthresh:
                self.state = CCState.CONGESTION_AVOIDANCE
        elif self.state == CCState.CONGESTION_AVOIDANCE:
            self.congestion_window += 1 / self.congestion_window

    def on_packet_loss(self):
        if self.state == CCState.SLOW_START:
            self.ssthresh = max(2, self.congestion_window // 2)
            self.congestion_window = 1
        elif self.state == CCState.CONGESTION_AVOIDANCE:
            self.ssthresh = max(2, self.congestion_window // 2)
            self.congestion_window = self.ssthresh
            self.state = CCState.FAST_RECOVERY

    def timeout(self):
        self.ssthresh = max(2, self.congestion_window // 2)
        self.congestion_window = 1
        self.state = CCState.SLOW_START

    def get_congestion_window(self):
        return self.congestion_window

    def get_state(self):
        return self.state