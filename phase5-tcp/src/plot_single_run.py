import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def plot_single_simulation(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)

    if not data.get("cwnd_log") and not data.get("rtt_log") and not data.get("rto_log"):
        print("No data to plot!")
        return

    # --- Plot 1: Congestion Window vs Time ---
    if data.get("cwnd_log"):
        times, cwnds = zip(*data["cwnd_log"])
        times = [float(t) for t in times]  # Convert times to float
        base_time = times[0]
        times = [t - base_time for t in times]  # Normalize to start from 0

        plt.figure(figsize=(10, 6))
        plt.plot(times, cwnds, marker='o', linestyle='-', linewidth=2)
        plt.xlabel("Time (s)", fontsize=14)
        plt.ylabel("Congestion Window Size", fontsize=14)
        plt.title("Congestion Window Size vs Time", fontsize=16)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(10))
        plt.savefig("cwnd_vs_time.png")
        plt.show()

    # --- Plot 2: RTT vs Time ---
    if data.get("rtt_log"):
        times, rtts = zip(*data["rtt_log"])
        times = [float(t) for t in times]  # Convert times to float
        base_time = times[0]
        times = [t - base_time for t in times]  # Normalize to start from 0

        plt.figure(figsize=(10, 6))
        plt.plot(times, rtts, marker='s', linestyle='-', linewidth=2, color='orange')
        plt.xlabel("Time (s)", fontsize=14)
        plt.ylabel("Sample RTT (seconds)", fontsize=14)
        plt.title("Sample RTT vs Time", fontsize=16)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(10))
        plt.savefig("rtt_vs_time.png")
        plt.show()

    # --- Plot 3: RTO vs Time ---
    if data.get("rto_log"):
        times, rtos = zip(*data["rto_log"])
        times = [float(t) for t in times]  # Convert times to float
        base_time = times[0]
        times = [t - base_time for t in times]  # Normalize to start from 0

        plt.figure(figsize=(10, 6))
        plt.plot(times, rtos, marker='^', linestyle='-', linewidth=2, color='green')
        plt.xlabel("Time (s)", fontsize=14)
        plt.ylabel("Retransmission Timeout (seconds)", fontsize=14)
        plt.title("RTO vs Time", fontsize=16)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(10))
        plt.savefig("rto_vs_time.png")
        plt.show()

import os

# Absolute path to the correct file
json_path = r"C:\Users\Ayush_pandey\OneDrive - UMass Lowell\Documents\GitHub\Spring-25---Network-Design\simulation_loss_0.0_delay_0.0.json"

if not os.path.exists(json_path):
    print(f"Error: File not found at {json_path}")
else:
    plot_single_simulation(json_path)