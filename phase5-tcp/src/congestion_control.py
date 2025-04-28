class CCState:
    WAITING = "waiting"
    SLOW_START = "slow_start"
    CONGESTION_AVOIDANCE = "congestion_avoidance"
    FAST_RECOVERY = "fast_recovery"

class CongestionControl:
    def __init__(self, logger=None):
        """Initialize congestion control parameters."""
        self.state = CCState.SLOW_START
        self.congestion_window = 1  # Start with an initial congestion window of 1 segment
        self.ssthresh = 64  # Default slow start threshold
        self.duplicate_acks = 0
        self.logger = logger  # Logger to track cwnd and state changes

        # Log the initial state and congestion window
        if self.logger:
            self.logger.log_cwnd(self.congestion_window)
            self.logger.log_state(self.state)

    def on_duplicate_ack(self):
        """Handles the receipt of a duplicate ACK."""
        if self.state == CCState.CONGESTION_AVOIDANCE or self.state == CCState.SLOW_START:
            self.duplicate_acks += 1
            if self.duplicate_acks == 3:
                # Triple Duplicate ACK detected - Enter Fast Recovery (Reno)
                self.ssthresh = max(2, self.congestion_window // 2)
                self.congestion_window = self.ssthresh + 3  # Inflate window
                self.state = CCState.FAST_RECOVERY
                if self.logger:
                    self.logger.log_cwnd(self.congestion_window)
                    self.logger.log_state(self.state)
                # Trigger Fast Retransmit (handled in tcp_connection)
                return True  # Indicate Fast Retransmit needed
        elif self.state == CCState.FAST_RECOVERY:
            # Inflate window for each additional duplicate ACK
            self.congestion_window += 1
            if self.logger:
                self.logger.log_cwnd(self.congestion_window)
        return False  # No Fast Retransmit needed yet

    def on_ack(self):
        """Called when a new ACK is received to update congestion window."""
        if self.congestion_window < self.ssthresh:
            # 🚀 Slow start: exponential growth
            self.congestion_window += 1
        else:
            # 🚀 Congestion avoidance: linear growth
            self.congestion_window += 1 / self.congestion_window

        # Log the updated congestion window and state
        if self.logger:
            self.logger.log_cwnd(self.congestion_window)
            self.logger.log_state(self.state)

    def on_ack_received(self, is_new_ack):
        """Handles receipt of a new ACK."""
        if is_new_ack:
            self.duplicate_acks = 0  # Reset count on new data ACKed
            if self.state == CCState.SLOW_START:
                self.congestion_window += 1
                if self.congestion_window >= self.ssthresh:
                    self.state = CCState.CONGESTION_AVOIDANCE
            elif self.state == CCState.CONGESTION_AVOIDANCE:
                # Increase linearly
                self.congestion_window += 1 / self.congestion_window
            elif self.state == CCState.FAST_RECOVERY:
                # New ACK received during Fast Recovery -> Deflate window, return to Congestion Avoidance
                self.congestion_window = self.ssthresh
                self.state = CCState.CONGESTION_AVOIDANCE

            # Log the updated congestion window and state
            if self.logger:
                self.logger.log_cwnd(self.congestion_window)
                self.logger.log_state(self.state)

    def on_timeout(self):
        """Handles a retransmission timeout event."""
        self.state = CCState.SLOW_START
        self.ssthresh = max(2, self.congestion_window // 2)
        self.congestion_window = 1
        self.duplicate_acks = 0

        # Log the timeout event
        if self.logger:
            self.logger.log_cwnd(self.congestion_window)
            self.logger.log_state(self.state)

    def on_packet_loss(self):
        """Handles a packet loss event (timeout)."""
        self.ssthresh = max(2, self.congestion_window // 2)
        self.congestion_window = 1
        self.state = CCState.SLOW_START
        self.duplicate_acks = 0

        # Log the packet loss event
        if self.logger:
            self.logger.log_cwnd(self.congestion_window)
            self.logger.log_state(self.state)

    def get_congestion_window(self):
        """Returns the current congestion window size."""
        return self.congestion_window

    def get_state(self):
        """Returns the current congestion control state."""
        return self.state