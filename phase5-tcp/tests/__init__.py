"""
This package contains unit tests for the phase5-tcp project.

Modules:
- test_tcp_segment: Tests for the TCPSegment class.
- test_tcp_connection: Tests for the SimpleTCPConnection class.
- test_rtt_estimator: Tests for the RTTEstimator class.
- test_congestion_control: Tests for the CongestionControl class.
"""

# Import all test modules to make them accessible when running the test suite
from .test_tcp_segment import *
from .test_tcp_connection import *
from .test_rtt_estimator import *
from .test_congestion_control import *