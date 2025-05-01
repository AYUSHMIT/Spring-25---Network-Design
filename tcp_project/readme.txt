============================================================
Simplified TCP Implementation over Unreliable UDP Channel
============================================================

Author: Ayush Pandey  
        Luis Daniel Peña Mateo
        Joseph Nguyen
        Parthaw Goswami

Course: Network Design - Spring 2025  
Project Phase: Final TCP Simulation (Phase 5)  
Language: Python 3.10+  
Platform: Windows/Linux  
Dependencies: None (Standard Library Only)

------------------------------------------------------------
1. Project Overview
------------------------------------------------------------

This project implements a simplified version of the Transmission Control Protocol (TCP)
on top of an unreliable UDP connection. It simulates core transport-layer features such as:

- 3-Way Handshake (SYN, SYN-ACK, ACK)
- Graceful Connection Teardown (FIN, ACK)
- Checksum-based Error Detection
- Reliable In-Order Data Transfer
- Timeout and RTT Estimation
- Sliding Window for Flow Control
- TCP Congestion Control (Slow Start, AIMD, Tahoe, Reno)

The goal is to simulate realistic TCP behavior under a lossy or delayed network
environment and generate performance plots for analysis.

------------------------------------------------------------
2. Directory Structure
------------------------------------------------------------

tcp_project/
├── sender.py                    # TCP sender (client)
├── receiver.py                  # TCP receiver (server)
├── tcp_segment.py               # TCP segment creation/parsing + checksum
├── utils.py                     # RTT estimator and Timer
├── congestion_control.py        # TCP congestion control logic
├── logger.py                    # Logs cwnd, RTT, RTO for plotting
├── logs/                        # Stores cwnd_log.txt, rtt_log.txt, etc.
│   ├── cwnd_log.txt
│   ├── rtt_log.txt
│   ├── rto_log.txt
│   └── simulation_log.txt
├── file_to_send.txt             # Input file sent by sender
├── received_file.txt            # Output file written by receiver
├── plot_cwnd_vs_time.py         # Plot congestion window over time
├── plot_rtt_vs_time.py          # Plot sample RTT over time
├── plot_rto_vs_time.py          # Plot RTO over time
└── README.txt                   # Project documentation (this file)

------------------------------------------------------------
3. How to Run
------------------------------------------------------------

Step 1: Open two terminal windows.

Step 2: Start the receiver (waits for connection):

    python receiver.py

Step 3: In the second terminal, start the sender:

    python sender.py

(If `python` command fails, use full Python path instead.)

The file `file_to_send.txt` will be transmitted to the receiver, which saves it as `received_file.txt`.

------------------------------------------------------------
4. Output and Plots
------------------------------------------------------------

After each run, logs will be saved in `logs/`:

- cwnd_log.txt       → Congestion window vs time
- rtt_log.txt        → Sample RTT measurements vs time
- rto_log.txt        → Retransmission timeout vs time
- simulation_log.txt → Events during connection

You can use the following scripts to generate performance plots:

    python plot_cwnd_vs_time.py
    python plot_rtt_vs_time.py
    python plot_rto_vs_time.py

------------------------------------------------------------
5. Notes
------------------------------------------------------------

- You can simulate packet loss and delay by implementing logic in `network_simulator.py`.
- By default, the network is perfect (no corruption/delay).
- Congestion control mode (Reno/Tahoe) can be selected inside `congestion_control.py`.
