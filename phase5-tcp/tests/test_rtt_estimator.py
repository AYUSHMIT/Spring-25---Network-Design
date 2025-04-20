import unittest
from src.rtt_estimator import RTTEstimator

class TestRTTEstimator(unittest.TestCase):

    def setUp(self):
        self.rtt_estimator = RTTEstimator()

    def test_initial_rtt(self):
        """Test initial RTT and deviation values."""
        self.assertIsNone(self.rtt_estimator.rtt)
        self.assertIsNone(self.rtt_estimator.dev)

    def test_update_rtt_first_sample(self):
        """Test RTT update with the first sample."""
        self.rtt_estimator.update(100)
        self.assertEqual(self.rtt_estimator.rtt, 100)
        self.assertEqual(self.rtt_estimator.dev, 50)  # Initial deviation is half of RTT

    def test_update_rtt_multiple_samples(self):
        """Test RTT update with multiple samples."""
        self.rtt_estimator.update(100)
        self.rtt_estimator.update(200)
        self.assertNotEqual(self.rtt_estimator.rtt, 100)
        self.assertNotEqual(self.rtt_estimator.dev, 50)

    def test_calculate_rto(self):
        """Test RTO calculation."""
        self.rtt_estimator.update(100)
        rto = self.rtt_estimator.get_timeout()
        self.assertEqual(rto, 100 + 4 * 50)  # RTO = RTT + 4 * DevRTT

# def test_karns_algorithm(self):
#     """Test Karn's algorithm (ignoring retransmitted segments)."""
#     self.rtt_estimator.update(100)
#     self.rtt_estimator.update(200)  # Simulate a retransmitted segment
#     self.assertEqual(self.rtt_estimator.rtt, 100)  # RTT should not update for retransmitted segments
    def test_exponential_backoff(self):
        """Test exponential backoff for RTO."""
        self.rtt_estimator.update(100)
        initial_rto = self.rtt_estimator.get_timeout()
        self.rtt_estimator.rtt *= 2  # Simulate timeout and backoff
        new_rto = self.rtt_estimator.get_timeout()
        self.assertGreater(new_rto, initial_rto)

if __name__ == '__main__':
    unittest.main()