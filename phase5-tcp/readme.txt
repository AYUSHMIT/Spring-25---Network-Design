# PHASE5-TCP PROJECT  
**Programming Project Phase 5 (Part 1): Implement TCP protocol over an unreliable UDP channel**  

---

## TEAM MEMBERS:
- **Ayush Pandey**  
- **Luis Daniel Peña Mateo**  
- **Joseph Nguyen**  
- **Parthaw Goswami**  

---

## PROJECT OVERVIEW:
This project implements a simplified version of the TCP protocol over an unreliable UDP channel. The implementation includes key TCP features such as congestion control, retransmissions, RTT estimation, and dynamic receiver window management. The goal is to simulate real-world TCP behavior under various network conditions, including packet loss, delays, and bit errors.

---

## FILES SUBMITTED AND THEIR PURPOSE:
### Core Source Files:
- **`src/tcp_segment.py`**:  
  - Defines the `TCPSegment` class for creating, packing, and unpacking TCP segments.  
  - Includes checksum calculations for error detection.  
  - Supports the `rwnd` field for receiver window size.  

- **`src/rtt_estimator.py`**:  
  - Implements the `RTTEstimator` class for estimating round-trip time (RTT) and RTT variance.  
  - Uses algorithms like Jacobson/Karels for adaptive timeout calculation.  

- **`src/congestion_control.py`**:  
  - Contains the `CongestionControl` class and `CCState` enum for managing congestion control states:  
    - Slow Start  
    - Congestion Avoidance  
    - Fast Recovery  
  - Implements logic for handling triple duplicate ACKs and timeouts.  

- **`src/tcp_connection.py`**:  
  - Implements the `SimpleTCPConnection` class for managing TCP state and logic.  
  - Features include:  
    - Retransmissions and Karn's Algorithm to prevent RTT updates for retransmitted segments.  
    - Buffering of out-of-order segments and duplicate ACK handling.  
    - Dynamic calculation of the receiver window (`rwnd`) and its inclusion in outgoing ACKs.  

- **`src/client.py`**:  
  - Main executable script for the TCP client application.  
  - Handles data transfer initiation and communication with the server.  

- **`src/server.py`**:  
  - Main executable script for the TCP server application.  
  - Listens for incoming connections and processes received data.  

- **`src/network_simulator.py`**:  
  - Simulates network conditions such as packet loss, delays, and bit errors.  
  - Provides APIs for introducing controlled network impairments.  

- **`src/utils.py`**:  
  - Shared utility functions for simulations, timers, and logging.  

### Supporting Files:
- **`tests/`**:  
  - Contains unit tests for all major components, including congestion control, RTT estimation, and TCP connection logic.  

- **`data/transfer_file.dat`**:  
  - Example large file (>= 500KB) for testing data transfer functionality.  

- **`plots/`**:  
  - Directory for saving performance plots generated during testing.  

- **`Design_Document.pdf`**:  
  - Detailed design document including flowcharts, code descriptions, and performance plots.  

- **`contribution.txt`**:  
  - Document outlining individual contributions to the project.  

- **`requirements.txt`**:  
  - Lists project dependencies, such as libraries required for implementation (e.g., `matplotlib`, `numpy`).  

---

## SETUP INSTRUCTIONS:
### Prerequisites:
- Python 3.8 or higher installed on your system.  
- `pip` package manager for installing dependencies.  

### Steps:
1. Clone the repository to your local machine:  
   ```bash
   git clone https://github.com/your-repo-url.git
   cd Spring-25---Network-Design/phase5-tcp
   ```

2. Create a virtual environment and activate it:  
   - On Windows:  
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - On macOS/Linux:  
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. Install the required dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

---

## EXECUTION INSTRUCTIONS:
### Running the TCP Client and Server:
1. Start the server:  
   ```bash
   python src/server.py
   ```

2. In a separate terminal, start the client:  
   ```bash
   python src/client.py
   ```

### Running Batch Simulations:
To run multiple simulations with varying parameters (e.g., loss rate):  
```bash
python src/batch_runner.py
```

---

## SCENARIO TESTING:
The following scenarios can be tested by modifying the `network_simulator.py` file or using its API to introduce specific network conditions:

1. **No Loss or Bit Error**:  
   - Ensure no packet loss or bit errors are introduced in the `NetworkSimulator` configuration.  
   - Run the client and server as described in the execution instructions.  

2. **ACK Packet Bit Error**:  
   - Simulate bit errors in ACK packets by modifying the `NetworkSimulator` to introduce errors in ACK segments.  
   - Observe retransmissions and error handling.  

3. **Data Packet Bit Error**:  
   - Simulate bit errors in data packets using the `NetworkSimulator`.  
   - Verify that corrupted packets are detected and retransmitted.  

4. **ACK Packet Loss**:  
   - Simulate dropped ACK packets in the `NetworkSimulator`.  
   - Observe how the sender handles retransmissions due to missing acknowledgments.  

5. **Data Packet Loss**:  
   - Simulate dropped data packets in the `NetworkSimulator`.  
   - Verify that the receiver requests retransmission of lost packets.  

6. **TCP-Specific Scenarios**:  
   - **Congestion Control**: Test TCP congestion control mechanisms such as Slow Start, Tahoe, and Reno by simulating varying network conditions.  
   - **Multiple Flow Fairness**: Run multiple client-server pairs simultaneously and observe fairness in bandwidth allocation.  
   - **Optional Attack/Resilience Tests**: If extra credit was attempted, simulate attacks (e.g., SYN flood) and observe resilience mechanisms.  

---

## FEATURES IMPLEMENTED:
1. **Congestion Control**:  
   - Implemented Slow Start, Congestion Avoidance, and Fast Recovery states.  
   - Added logic to handle triple duplicate ACKs and timeouts for retransmissions.  

2. **Karn's Algorithm**:  
   - Prevented RTT updates for ACKs corresponding to retransmitted segments.  

3. **Out-of-Order Segment Handling**:  
   - Buffered out-of-order segments and processed them when the missing sequence number was received.  

4. **Dynamic Receiver Window (`rwnd`)**:  
   - Calculated available buffer space dynamically and included it in outgoing ACKs.  

5. **Retransmission Logic**:  
   - Added logic to retransmit segments on triple duplicate ACKs or timeouts.  

---

## RUNNING TESTS:
Run all unit tests using the provided `run_tests.py` script:  
```bash
python run_tests.py
```

Alternatively, use `unittest` or `pytest`:  
```bash
python -m unittest discover tests
pytest tests/
```

---

## PERFORMANCE PLOTS:
The following performance plots can be generated using the project:  

1. **TCP Performance with Varying Loss/Error Rate**:  
   - X-axis: Intentional loss probability (0% - 70% in 5% increments).  
   - Y-axis: File Transfer Completion Time.  

2. **Completion Time vs Timeout Value**:  
   - Fixed loss/error probability (e.g., 20%).  
   - X-axis: Retransmission Timeout (10ms – 100ms).  
   - Y-axis: File Transfer Completion Time.  

3. **Completion Time vs Window Size**:  
   - Fixed loss/error probability (e.g., 20%).  
   - X-axis: Window size (1, 2, 5, 10, 20, 30, 40, 50).  
   - Y-axis: File Transfer Completion Time.  

4. **Protocol Performance Comparison**:  
   - Compare performance under the same conditions.  
   - X-axis: Protocols (Phase 2, Phase 3, Phase 4, TCP).  
   - Y-axis: File Transfer Completion Time.  

5. **Additional Charts**:  
   - Window size (`cwnd`) vs time.  
   - Sample RTT vs time.  
   - RTO vs time.  
   - (Optional) Fairness or throughput comparison for multi-flow experiments.  

---

## ACKNOWLEDGMENTS:
This project is inspired by the need to understand TCP's inner workings and its implementation in real-world applications.  
Special thanks to the contributors for their efforts in designing and implementing this project.  

---

## LICENSE:
This project is licensed under the MIT License. See the LICENSE file for details.