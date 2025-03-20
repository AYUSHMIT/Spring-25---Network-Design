#!/usr/bin/env python3
"""
Receiver-Driven RDT 3.0 Experiment and Graphing Script

This script tests the receiver-driven protocol under different loss rates (0% to 60% in 5% increments)
and for each simulation option (1: No error, 2: ACK bit error, 3: Data packet error, 
4: ACK packet loss, 5: Data packet loss).

For each combination, the experiment runs 5 times and averages the metrics:
  - Completion Time (seconds)
  - Total Retransmissions
  - Throughput (bytes/second)

The script plots averaged metrics versus loss rate, one line per option.

Usage:
    python3 receiver_driven_experiment.py

Make sure your receiver-driven server (`server_rd.py`) is running before starting.
"""

import time
import csv
import matplotlib.pyplot as plt
import subprocess
import os

RUNS_PER_CONFIG = 5
loss_rates = list(range(0, 65, 5))
options = [1, 2, 3, 4, 5]

filename = "image.jpg"
receiver_ip = "127.0.0.1"
receiver_port = 10000
server_script = "server_rd.py"

# Ensure server is running before starting experiments
def start_server():
    print("Starting receiver-driven server...")
    subprocess.Popen(["python3", server_script, "received_file.jpg", receiver_ip, "10", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)  # Allow time for server startup

# Kill any running instances to prevent conflicts
def stop_server():
    os.system("pkill -f server_rd.py")
    time.sleep(2)  # Ensure process is killed

# Restart server before experiments
stop_server()
start_server()

# Overwrite performance_data.csv with header
with open("performance_data.csv", "w") as f:
    f.write("Option,LossRate,CompletionTime,Throughput,Retransmissions\n")

results = {opt: {"time": [], "retrans": [], "throughput": []} for opt in options}

for opt in options:
    print(f"\nTesting Option {opt}")
    for lr in loss_rates:
        total_time, total_retrans, total_tput = 0, 0, 0

        for _ in range(RUNS_PER_CONFIG):
            cmd = ["python3", "client_rd.py", filename, receiver_ip, str(lr), str(opt)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            output = stdout.decode().strip().split("\n")
            
            if proc.returncode != 0:
                print(f"Error running client_rd.py: {stderr.decode().strip()}")
                continue
            
            # Extracting metrics from last three lines
            try:
                comp_time = float(output[-3].split(':')[1].strip().split()[0])
                retrans = int(output[-2].split(':')[1].strip())
                throughput = float(output[-1].split(':')[1].strip().split()[0])
            except (IndexError, ValueError):
                print("Error parsing client output:", output)
                continue
            
            total_time += comp_time
            total_retrans += retrans
            total_tput += throughput
            time.sleep(1)  # brief pause between runs

        avg_time = total_time / RUNS_PER_CONFIG
        avg_retrans = total_retrans / RUNS_PER_CONFIG
        avg_tput = total_tput / RUNS_PER_CONFIG

        results[opt]["time"].append(avg_time)
        results[opt]["retrans"].append(avg_retrans)
        results[opt]["throughput"].append(avg_tput)

        with open("performance_data.csv", "a") as f:
            f.write(f"{opt},{lr},{avg_time:.2f},{avg_tput:.2f},{avg_retrans:.2f}\n")

        print(f"Loss: {lr}% | Time: {avg_time:.2f}s | Retrans: {avg_retrans:.2f} | Throughput: {avg_tput:.2f} bytes/s")

# Stop server after experiments
stop_server()

# Plotting Results
plt.figure(figsize=(12, 8))

# Completion Time
plt.subplot(3, 1, 1)
for opt in options:
    plt.plot(loss_rates, results[opt]["time"], label=f"Option {opt}", marker='o')
plt.xlabel("Loss Rate (%)")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs. Loss Rate")
plt.legend()
plt.grid()

# Retransmissions
plt.subplot(3, 1, 2)
for opt in options:
    plt.plot(loss_rates, results[opt]["retrans"], label=f"Option {opt}", marker='o')
plt.xlabel("Loss Rate (%)")
plt.ylabel("Retransmissions")
plt.title("Retransmissions vs. Loss Rate")
plt.legend()
plt.grid()

# Throughput
plt.subplot(3, 1, 3)
for opt in options:
    plt.plot(loss_rates, results[opt]["throughput"], label=f"Option {opt}", marker='o')
plt.xlabel("Loss Rate (%)")
plt.ylabel("Throughput (bytes/s)")
plt.title("Throughput vs. Loss Rate")
plt.legend()
plt.grid()

plt.tight_layout()
plt.show()
