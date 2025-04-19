import unittest
from src.congestion_control import CongestionControl, CCState

class TestCongestionControl(unittest.TestCase):

    def setUp(self):
        self.cc = CongestionControl()

    def test_initial_state(self):
        """Test the initial state of the congestion control."""
        self.assertEqual(self.cc.state, CCState.SLOW_START)
        self.assertEqual(self.cc.congestion_window, 1)
        self.assertEqual(self.cc.ssthresh, 64)

    def test_congestion_window_increase_slow_start(self):
        """Test congestion window increase in Slow Start."""
        self.cc.state = CCState.SLOW_START
        initial_cwnd = self.cc.congestion_window
        self.cc.on_ack_received()
        self.assertEqual(self.cc.congestion_window, initial_cwnd + 1)

    def test_congestion_window_increase_congestion_avoidance(self):
        """Test congestion window increase in Congestion Avoidance."""
        self.cc.state = CCState.CONGESTION_AVOIDANCE
        self.cc.congestion_window = 10
        initial_cwnd = self.cc.congestion_window
        self.cc.on_ack_received()
        self.assertGreater(self.cc.congestion_window, initial_cwnd)
        self.assertAlmostEqual(self.cc.congestion_window, initial_cwnd + 1 / initial_cwnd, places=5)

    def test_congestion_window_decrease_on_loss(self):
        """Test congestion window decrease on packet loss."""
        self.cc.congestion_window = 10
        self.cc.on_packet_loss()
        self.assertEqual(self.cc.ssthresh, 5)  # ssthresh = cwnd / 2
        self.assertEqual(self.cc.congestion_window, 1)  # cwnd resets to 1

    def test_state_transition_to_congestion_avoidance(self):
        """Test state transition from Slow Start to Congestion Avoidance."""
        self.cc.state = CCState.SLOW_START
        self.cc.congestion_window = self.cc.ssthresh
        self.cc.on_ack_received()
        self.assertEqual(self.cc.state, CCState.CONGESTION_AVOIDANCE)

    def test_fast_recovery_on_triple_duplicate_acks(self):
        """Test Fast Recovery behavior on triple duplicate ACKs."""
        self.cc.state = CCState.CONGESTION_AVOIDANCE
        self.cc.congestion_window = 10
        self.cc.on_packet_loss()  # Simulate triple duplicate ACKs
        self.assertEqual(self.cc.state, CCState.SLOW_START)
        self.assertEqual(self.cc.ssthresh, 5)  # ssthresh = cwnd / 2
        self.assertEqual(self.cc.congestion_window, 1)  # cwnd resets to 1

    def test_cwnd_reset_on_timeout(self):
        """Test congestion window reset on timeout."""
        self.cc.congestion_window = 10
        self.cc.on_timeout()
        self.assertEqual(self.cc.congestion_window, 1)  # cwnd resets to 1
        self.assertEqual(self.cc.ssthresh, 5)  # ssthresh = cwnd / 2

    def test_state_persistence(self):
        """Test that the state persists correctly across operations."""
        self.cc.state = CCState.CONGESTION_AVOIDANCE
        self.cc.on_ack_received()
        self.assertEqual(self.cc.state, CCState.CONGESTION_AVOIDANCE)

if __name__ == '__main__':
    unittest.main()