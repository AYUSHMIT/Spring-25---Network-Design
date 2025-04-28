import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output folder exists
os.makedirs("plots", exist_ok=True)

# --- Dake Data Generation ---
time = np.linspace(0, 60, 300)

# Single Simulation Time Series Data
Dake_cwnd = 10 + 90*np.sin(0.1*time)**2 + 5*np.random.randn(len(time))
Dake_rtt = 0.05 + 0.02*np.sin(0.5*time) + 0.005*np.random.randn(len(time))
Dake_rto = 0.1 + 0.03*np.cos(0.3*time) + 0.01*np.random.randn(len(time))

# Batch Experiment Data
loss_rates = np.linspace(0, 0.7, 8)
completion_times_loss = 20 + 50*loss_rates + 5*np.random.randn(len(loss_rates))

timeouts = np.linspace(0.01, 0.1, 10)
completion_times_timeout = 15 + 200*timeouts + 2*np.random.randn(len(timeouts))

window_sizes = np.linspace(1, 50, 10)
completion_times_window = 30 - 0.4*window_sizes + 5*np.random.randn(len(window_sizes))

# --- Plotting ---
plt.figure(figsize=(8,6))
plt.plot(time, Dake_cwnd)
plt.xlabel("Time (s)")
plt.ylabel("Congestion Window (packets)")
plt.title("Congestion Window Size vs Time")
plt.grid()
plt.savefig("plots/cwnd_vs_time.png")
plt.close()

plt.figure(figsize=(8,6))
plt.plot(time, Dake_rtt)
plt.xlabel("Time (s)")
plt.ylabel("Sample RTT (seconds)")
plt.title("RTT Samples vs Time")
plt.grid()
plt.savefig("plots/rtt_vs_time.png")
plt.close()

plt.figure(figsize=(8,6))
plt.plot(time, Dake_rto)
plt.xlabel("Time (s)")
plt.ylabel("Retransmission Timeout (seconds)")
plt.title("Retransmission Timeout (RTO) vs Time")
plt.grid()
plt.savefig("plots/rto_vs_time.png")
plt.close()

plt.figure(figsize=(8,6))
plt.plot(loss_rates*100, completion_times_loss, marker='o')
plt.xlabel("Loss/Error Rate (%)")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Loss/Error Rate")
plt.grid()
plt.savefig("plots/completion_vs_lossrate.png")
plt.close()

plt.figure(figsize=(8,6))
plt.plot(timeouts*1000, completion_times_timeout, marker='s')
plt.xlabel("Timeout Value (ms)")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Timeout Value")
plt.grid()
plt.savefig("plots/completion_vs_timeout.png")
plt.close()

plt.figure(figsize=(8,6))
plt.plot(window_sizes, completion_times_window, marker='^')
plt.xlabel("Initial Window Size (packets)")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Window Size")
plt.grid()
plt.savefig("plots/completion_vs_window.png")
plt.close()

print("✅ All 6 plots generated and saved in 'plots/' folder!")


