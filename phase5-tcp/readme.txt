PHASE5-TCP PROJECT

OVERVIEW:
The Phase5-TCP project is a Python-based implementation of the Transmission Control Protocol (TCP). 
It provides a detailed simulation of TCP's core functionalities, including segment handling, 
round-trip time (RTT) estimation, congestion control, and reliable data transfer over an unreliable UDP channel. 
The project includes client and server applications to demonstrate TCP communication and supports testing under 
various network conditions, such as packet loss and delays.

This project is designed to help understand TCP's inner workings and its real-world implementation.

---

DIRECTORY STRUCTURE:
- src/: Contains the source code for the TCP implementation.
  - tcp_segment.py: Defines the TCPSegment class for segment packing/unpacking and checksum calculations.
  - rtt_estimator.py: Implements the RTTEstimator class for estimating round-trip time and managing RTT variance.
  - congestion_control.py: Contains the CongestionControl class and CCState enum for managing congestion control algorithms.
  - tcp_connection.py: Implements the SimpleTCPConnection class for TCP logic and state management.
  - client.py: Main executable script for the TCP client application.
  - server.py: Main executable script for the TCP server application.
  - network_simulator.py: Simulates network conditions like packet loss and delays.
  - utils.py: Shared utility functions for simulations and timers.

- tests/: Contains unit tests for the project components.
  - test_tcp_segment.py: Unit tests for the TCPSegment class.
  - test_rtt_estimator.py: Unit tests for the RTTEstimator class.
  - test_congestion_control.py: Unit tests for the CongestionControl class.
  - test_tcp_connection.py: Unit tests for the SimpleTCPConnection class.

- data/: Directory for test data, including a large file for transfer testing.
  - transfer_file.dat: Example large file (>= 500KB) for testing data transfer functionality.

- plots/: Directory for saving performance plots generated during testing.

- Design_Document.pdf: Detailed design document including flowcharts, code descriptions, and performance plots.

- contribution.txt: Document outlining individual contributions to the project.

- requirements.txt: Lists project dependencies, such as libraries required for implementation (e.g., matplotlib).

---

SETUP INSTRUCTIONS:
1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Create a virtual environment and activate it:
   - On Windows:
     ```
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     python -m venv .venv
     source .venv/bin/activate
     ```
4. Install the required dependencies using:
pip install -r requirements.txt


---

USAGE:
To run the TCP client and server applications:
1. Start the server by executing:

python server.py

2. In a separate terminal, start the client by executing:
python client.py

python client.py


---

SCENARIO TESTING:
- Test various scenarios by modifying the client and server scripts to simulate different network conditions.
- Use the NetworkSimulator class to introduce packet loss, delays, and bit errors.
- Analyze performance metrics using the plots generated in the plots/ directory.

---

RUNNING TESTS:
Run all unit tests using the provided run_tests.py script:
python run_tests.py


Alternatively, use unittest or pytest:
python -m unittest discover tests pytest tests/


---

ACKNOWLEDGMENTS:
This project is inspired by the need to understand TCP's inner workings and its implementation in real-world applications.
Special thanks to the contributors for their efforts in designing and implementing this project.

---

LICENSE:
This project is licensed under the MIT License. See the LICENSE file for details.