import unittest
from src.rtt_estimator import RTTEstimator

class TestRTTEstimator(unittest.TestCase):
    """
    Unit tests for the RTTEstimator class.
    These tests verify the behavior of RTT estimation, deviation calculation,
    RTO (Retransmission Timeout) calculation, and exponential backoff.
    """

    def setUp(self):
        """
        Set up a new RTTEstimator instance before each test.
        """
        self.rtt_estimator = RTTEstimator()

    def test_initial_rtt(self):
        """
        Test initial RTT and deviation values.
        Verify that RTT and deviation are None before any samples are provided.
        """
        self.assertIsNone(self.rtt_estimator.rtt)  # RTT should be None initially
        self.assertIsNone(self.rtt_estimator.dev)  # Deviation should be None initially

    def test_update_rtt_first_sample(self):
        """
        Test RTT update with the first sample.
        Verify that RTT and deviation are correctly initialized with the first sample.
        """
        self.rtt_estimator.update(100)  # Provide the first RTT sample
        self.assertEqual(self.rtt_estimator.rtt, 100)  # RTT should match the first sample
        self.assertEqual(self.rtt_estimator.dev, 50)  # Initial deviation is half of RTT

    def test_update_rtt_multiple_samples(self):
        """
        Test RTT update with multiple samples.
        Verify that RTT and deviation are updated correctly with additional samples.
        """
        self.rtt_estimator.update(100)  # First RTT sample
        self.rtt_estimator.update(200)  # Second RTT sample
        self.assertNotEqual(self.rtt_estimator.rtt, 100)  # RTT should update
        self.assertNotEqual(self.rtt_estimator.dev, 50)  # Deviation should update

    def test_calculate_rto(self):
        """
        Test RTO (Retransmission Timeout) calculation.
        Verify that RTO is calculated as RTT + 4 * DevRTT.
        """
        self.rtt_estimator.update(100)  # Provide an RTT sample
        rto = self.rtt_estimator.get_timeout()  # Calculate RTO
        self.assertEqual(rto, 100 + 4 * 50)  # RTO = RTT + 4 * DevRTT

    def test_exponential_backoff(self):
        """
        Test exponential backoff for RTO.
        Verify that RTO increases after a timeout (simulated by doubling RTT).
        """
        self.rtt_estimator.update(100)  # Provide an RTT sample
        initial_rto = self.rtt_estimator.get_timeout()  # Get initial RTO
        self.rtt_estimator.rtt *= 2  # Simulate timeout by doubling RTT
        new_rto = self.rtt_estimator.get_timeout()  # Get new RTO after backoff
        self.assertGreater(new_rto, initial_rto)  # New RTO should be greater than initial RTO

if __name__ == '__main__':
    unittest.main()