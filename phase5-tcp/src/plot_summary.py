import json
import matplotlib.pyplot as plt

def plot_summary(summary_file):
    with open(summary_file, "r") as f:
        summary_data = json.load(f)

    if not summary_data:
        print("Summary file is empty!")
        return

    loss_rates = []
    delays = []
    completion_times = []

    for entry in summary_data:
        if entry["completion_time"] is not None:
            loss_rates.append(entry["loss_rate"] * 100)  # convert to %
            delays.append(entry["max_delay"])
            completion_times.append(entry["completion_time"])

    if not completion_times:
        print("No successful simulation data to plot!")
        return

    # --- Plot: Completion Time vs Loss Rate ---
    plt.figure()
    plt.plot(loss_rates, completion_times, marker='o')
    plt.xlabel("Loss Rate (%)")
    plt.ylabel("Completion Time (s)")
    plt.title("Completion Time vs Loss Rate")
    plt.grid(True)
    plt.savefig("completion_vs_lossrate.png")
    plt.show()

    # --- Plot: Completion Time vs Max Delay ---
    plt.figure()
    plt.plot(delays, completion_times, marker='o', color='red')
    plt.xlabel("Max Delay (s)")
    plt.ylabel("Completion Time (s)")
    plt.title("Completion Time vs Max Delay")
    plt.grid(True)
    plt.savefig("completion_vs_maxdelay.png")
    plt.show()

# Example:
plot_summary("summary.json")

