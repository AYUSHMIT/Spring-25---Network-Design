import os
import json  # Import json for reading the summary file
import matplotlib.pyplot as plt  # Import matplotlib for plotting

def plot_window_summary(summary_file="c:/Users/Ayush_pandey/OneDrive - UMass Lowell/Documents/GitHub/Spring-25---Network-Design/completion_time_vs_window_size.json"):
    if not os.path.exists(summary_file):
        print(f"Error: Summary file '{summary_file}' not found. Please run batch_runner.py first.")
        return

    with open(summary_file, "r") as f:
        results = json.load(f)

    window_sizes = [x[0] for x in results if x[1] is not None]
    completion_times = [x[1] for x in results if x[1] is not None]

    plt.figure(figsize=(10, 6))
    plt.plot(window_sizes, completion_times, marker='s', linestyle='-')
    plt.xlabel("Initial Window Size (segments)")
    plt.ylabel("Completion Time (s)")
    plt.title("Completion Time vs Initial Window Size")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("completion_vs_initial_window.png")
    plt.show()

if __name__ == "__main__":
    plot_window_summary()