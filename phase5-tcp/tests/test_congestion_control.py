import unittest
from src.congestion_control import CongestionControl, CCState

class TestCongestionControl(unittest.TestCase):
    """
    Unit tests for the CongestionControl class.
    These tests verify the behavior of congestion control mechanisms such as Slow Start,
    Congestion Avoidance, and Fast Recovery.
    """

    def setUp(self):
        """
        Set up a new CongestionControl instance before each test.
        """
        self.cc = CongestionControl()

    def test_initial_state(self):
        """
        Test the initial state of the congestion control.
        Verify that the state is SLOW_START, the congestion window (cwnd) is 1,
        and the slow start threshold (ssthresh) is 64.
        """
        self.assertEqual(self.cc.state, CCState.SLOW_START)
        self.assertEqual(self.cc.congestion_window, 1)
        self.assertEqual(self.cc.ssthresh, 64)

    def test_congestion_window_increase_slow_start(self):
        """
        Test congestion window increase in Slow Start.
        Verify that the congestion window grows exponentially during Slow Start.
        """
        self.cc.state = CCState.SLOW_START
        initial_cwnd = self.cc.congestion_window
        self.cc.on_ack_received(is_new_ack=True)  # Simulate receiving a new ACK
        self.assertEqual(self.cc.congestion_window, initial_cwnd + 1)

    def test_congestion_window_increase_congestion_avoidance(self):
        """
        Test congestion window increase in Congestion Avoidance.
        Verify that the congestion window grows linearly during Congestion Avoidance.
        """
        self.cc.state = CCState.CONGESTION_AVOIDANCE
        self.cc.congestion_window = 10
        initial_cwnd = self.cc.congestion_window
        self.cc.on_ack_received(is_new_ack=True)  # Simulate receiving a new ACK
        self.assertGreater(self.cc.congestion_window, initial_cwnd)
        self.assertAlmostEqual(self.cc.congestion_window, initial_cwnd + 1 / initial_cwnd, places=5)

    def test_congestion_window_decrease_on_loss(self):
        """
        Test congestion window decrease on packet loss.
        Verify that the congestion window resets to 1 and the slow start threshold
        is halved when a timeout occurs.
        """
        self.cc.congestion_window = 10
        self.cc.on_timeout()  # Simulate a timeout (packet loss)
        self.assertEqual(self.cc.ssthresh, 5)  # ssthresh = cwnd / 2
        self.assertEqual(self.cc.congestion_window, 1)  # cwnd resets to 1

    def test_state_transition_to_congestion_avoidance(self):
        """
        Test state transition from Slow Start to Congestion Avoidance.
        Verify that the state changes to Congestion Avoidance when the congestion
        window exceeds the slow start threshold.
        """
        self.cc.state = CCState.SLOW_START
        self.cc.congestion_window = self.cc.ssthresh
        self.cc.on_ack_received(is_new_ack=True)  # Simulate receiving a new ACK
        self.assertEqual(self.cc.state, CCState.CONGESTION_AVOIDANCE)

    def test_fast_recovery_on_triple_duplicate_acks(self):
        """
        Test Fast Recovery behavior on triple duplicate ACKs.
        Verify that the state transitions to FAST_RECOVERY, the slow start threshold
        is halved, and the congestion window is inflated.
        """
        self.cc.state = CCState.CONGESTION_AVOIDANCE
        self.cc.congestion_window = 10
        for _ in range(3):  # Simulate triple duplicate ACKs
            self.cc.on_duplicate_ack()
        self.assertEqual(self.cc.state, CCState.FAST_RECOVERY)
        self.assertEqual(self.cc.ssthresh, 5)  # ssthresh = cwnd / 2
        self.assertEqual(self.cc.congestion_window, 8)  # cwnd = ssthresh + 3

    def test_cwnd_reset_on_timeout(self):
        """
        Test congestion window reset on timeout.
        Verify that the congestion window resets to 1 and the slow start threshold
        is halved when a timeout occurs.
        """
        self.cc.congestion_window = 10
        self.cc.on_timeout()
        self.assertEqual(self.cc.congestion_window, 1)  # cwnd resets to 1
        self.assertEqual(self.cc.ssthresh, 5)  # ssthresh = cwnd / 2

    def test_state_persistence(self):
        """
        Test that the state persists correctly across operations.
        Verify that the state remains in Congestion Avoidance after receiving a new ACK.
        """
        self.cc.state = CCState.CONGESTION_AVOIDANCE
        self.cc.on_ack_received(is_new_ack=True)  # Simulate receiving a new ACK
        self.assertEqual(self.cc.state, CCState.CONGESTION_AVOIDANCE)

if __name__ == '__main__':
    unittest.main()