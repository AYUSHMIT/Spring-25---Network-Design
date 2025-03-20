#!/usr/bin/env python3
"""
Author: Joseph Nguyen
Description: Automates experiments for sender-driven RDT 3.0.
For each option (1–5) and for loss rates from 0% to 60% (in 5% increments),
it runs 5 trials, averages the completion time (and other metrics), and writes
one averaged row per condition to performance_data.csv.
Usage:
    python experiment.py
Ensure that the server is running before starting the experiments.
"""

import time, client

loss_rates = list(range(0, 65, 5))
options = [1, 2, 3, 4, 5]
filename = "sample.jpg"      # File to send (ensure it exists)
server_ip = "127.0.0.1"        # Adjust if needed
mode = "sender_driven"

# Overwrite performance_data.csv with header
with open("performance_data.csv", "w") as f:
    f.write("Option,LossRate,CompletionTime,Throughput,DataRetrans,ACKRetrans,ACKEfficiency\n")

for opt in options:
    print(f"\nRunning experiments for Option {opt}")
    for lr in loss_rates:
        print(f"  Loss rate: {lr}%")
        sum_time = 0.0
        sum_tput = 0.0
        sum_data_retx = 0
        sum_ack_retx = 0
        sum_ack_eff = 0.0
        runs = 5
        for i in range(runs):
            client.data_retransmissions = 0
            client.ack_retransmissions = 0
            client.SIM_LOSS_RATE = lr / 100.0
            metrics = client.send_file(filename, (server_ip, 10000), mode, opt)
            # metrics: (completion_time, throughput, data_retrans, ack_retrans, ack_efficiency)
            sum_time += metrics[0]
            sum_tput += metrics[1]
            sum_data_retx += metrics[2]
            sum_ack_retx += metrics[3]
            sum_ack_eff += metrics[4]
            time.sleep(1)
        avg_time = sum_time / runs
        avg_tput = sum_tput / runs
        avg_data_retx = sum_data_retx / runs
        avg_ack_retx = sum_ack_retx / runs
        avg_ack_eff = sum_ack_eff / runs
        print(f"    Averaged: time={avg_time:.2f}s, throughput={avg_tput:.2f}B/s, data_retrans={avg_data_retx:.1f}, ACK retrans={avg_ack_retx:.1f}")
        with open("performance_data.csv", "a") as f:
            f.write(f"{opt},{lr},{avg_time},{avg_tput},{avg_data_retx},{avg_ack_retx},{avg_ack_eff}\n")
print("\nAll experiments completed.")