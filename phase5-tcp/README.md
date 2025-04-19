# phase5-tcp Project

## Overview
The phase5-tcp project is a Python implementation of the Transmission Control Protocol (TCP). It aims to provide a comprehensive understanding of TCP's functionality, including segment handling, round-trip time estimation, congestion control, and connection management. This project includes both client and server applications to demonstrate TCP communication.

## Directory Structure
- **src/**: Contains the source code for the TCP implementation.
  - **tcp_segment.py**: Defines the `TCPSegment` class for segment packing/unpacking and checksum calculations.
  - **rtt_estimator.py**: Implements the `RTTEstimator` class for estimating round-trip time and managing RTT variance.
  - **congestion_control.py**: Contains the `CongestionControl` class and `CCState` enum for managing congestion control algorithms.
  - **tcp_connection.py**: Implements the `SimpleTCPConnection` class for TCP logic and state management.
  - **client.py**: Main executable script for the TCP client application.
  - **server.py**: Main executable script for the TCP server application.
  - **utils.py**: Shared utility functions for simulations and timers.

- **tests/**: Contains unit tests for the project components.
  - **test_tcp_segment.py**: Unit tests for the `TCPSegment` class.
  - **test_rtt_estimator.py**: Unit tests for the `RTTEstimator` class.
  - **test_congestion_control.py**: Unit tests for the `CongestionControl` class.
  - **test_tcp_connection.py**: Unit tests for the `SimpleTCPConnection` class.

- **data/**: Directory for test data, including a large file for transfer testing.
  - **transfer_file.dat**: Example large file (>= 500KB) for testing data transfer functionality.

- **plots/**: Directory for saving performance plots generated during testing.
  - Contains various plots related to TCP performance metrics.

- **Design_Document.pdf**: Detailed design document including flowcharts, code descriptions, and performance plots.

- **contribution.txt**: Document outlining individual contributions to the project.

- **requirements.txt**: Lists project dependencies, such as libraries required for implementation (e.g., matplotlib).

## Setup Instructions
1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Install the required dependencies using:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the TCP client and server applications:
1. Start the server by executing:
   ```
   python src/server.py
   ```
2. In a separate terminal, start the client by executing:
   ```
   python src/client.py
   ```

## Scenario Testing
- Test various scenarios by modifying the client and server scripts to simulate different network conditions.
- Use the provided plots to analyze performance metrics and behavior under different conditions.

## Acknowledgments
This project is inspired by the need to understand TCP's inner workings and its implementation in real-world applications.