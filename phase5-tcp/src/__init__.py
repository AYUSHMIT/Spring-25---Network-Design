"""
This package contains the core implementation of the phase5-tcp project.

Modules:
- tcp_segment: Defines the TCPSegment class for handling TCP segments.
- tcp_connection: Implements the SimpleTCPConnection class for custom TCP logic.
- rtt_estimator: Provides the RTTEstimator class for RTT and RTO calculations.
- congestion_control: Implements the CongestionControl class for TCP congestion control.
- network_simulator: Simulates network conditions like packet loss and delays.
"""

# Import key classes for easier access when importing the package
from .tcp_segment import TCPSegment
from .tcp_connection import SimpleTCPConnection
from .rtt_estimator import RTTEstimator
from .congestion_control import CongestionControl
from .network_simulator import NetworkSimulator