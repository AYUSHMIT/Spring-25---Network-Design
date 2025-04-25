import json
import matplotlib.pyplot as plt

def plot_cwnd_vs_time(data_file):
    with open(data_file, "r") as f:
        data = json.load(f)

    cwnd_log = data["cwnd_log"]
    times = [entry[0] for entry in cwnd_log]
    cwnd_values = [entry[1] for entry in cwnd_log]

    plt.plot(times, cwnd_values, label="cwnd")
    plt.title("Congestion Window (cwnd) vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("cwnd")
    plt.legend()
    plt.savefig("cwnd_vs_time.png")  # Save in the current folder
    plt.show()

def plot_rtt_vs_time(data_file):
    with open(data_file, "r") as f:
        data = json.load(f)

    rtt_log = data["rtt_log"]
    times = [entry[0] for entry in rtt_log]
    rtt_values = [entry[1] for entry in rtt_log]

    plt.plot(times, rtt_values, label="RTT")
    plt.title("RTT vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("RTT (s)")
    plt.legend()
    plt.savefig("rtt_vs_time.png")  # Save in the current folder
    plt.show()

# Example: Generate plots
plot_cwnd_vs_time("./simulation_loss_0.1_delay_0.1.json")  # Adjusted path
plot_rtt_vs_time("./simulation_loss_0.1_delay_0.1.json")  # Adjusted path