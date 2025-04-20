PHASE5-TCP PROJECT  
Programming Project Phase 5 (Part 1): Implement TCP protocol over an unreliable UDP channel  

---

### TEAM MEMBERS:
- Ayush Pandey  
- Luis Daniel Peña Mateo  
- Joseph Nguyen  
- Parthaw Goswami  

---

### FILES SUBMITTED AND THEIR PURPOSE:
- **src/tcp_segment.py**: Defines the `TCPSegment` class for segment packing/unpacking and checksum calculations.  
- **src/rtt_estimator.py**: Implements the `RTTEstimator` class for estimating round-trip time and managing RTT variance.  
- **src/congestion_control.py**: Contains the `CongestionControl` class and `CCState` enum for managing congestion control algorithms.  
- **src/tcp_connection.py**: Implements the `SimpleTCPConnection` class for TCP logic and state management.  
- **src/client.py**: Main executable script for the TCP client application.  
- **src/server.py**: Main executable script for the TCP server application.  
- **src/network_simulator.py**: Simulates network conditions like packet loss, delays, and bit errors.  
- **src/utils.py**: Shared utility functions for simulations and timers.  
- **tests/**: Contains unit tests for all major components of the project.  
- **data/transfer_file.dat**: Example large file (>= 500KB) for testing data transfer functionality.  
- **plots/**: Directory for saving performance plots generated during testing.  
- **Design_Document.pdf**: Detailed design document including flowcharts, code descriptions, and performance plots.  
- **contribution.txt**: Document outlining individual contributions to the project.  
- **requirements.txt**: Lists project dependencies, such as libraries required for implementation (e.g., `matplotlib`).  

---

### SETUP INSTRUCTIONS:
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
   ```
   pip install -r requirements.txt
   ```

---

### EXECUTION INSTRUCTIONS:
To run the TCP client and server applications:  
1. Start the server by executing:  
   ```
   python src/server.py
   ```
2. In a separate terminal, start the client by executing:  
   ```
   python src/client.py
   ```

---

### SCENARIO TESTING:
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

### RUNNING TESTS:
Run all unit tests using the provided `run_tests.py` script:  
```
python run_tests.py
```

Alternatively, use `unittest` or `pytest`:  
```
python -m unittest discover tests
pytest tests/
```

---

### ACKNOWLEDGMENTS:
This project is inspired by the need to understand TCP's inner workings and its implementation in real-world applications.  
Special thanks to the contributors for their efforts in designing and implementing this project.  

---

### LICENSE:
This project is licensed under the MIT License. See the LICENSE file for details.  