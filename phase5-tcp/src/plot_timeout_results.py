import os
import json
import matplotlib.pyplot as plt

def plot_window_summary(summary_file="c:/Users/Ayush_pandey/OneDrive - UMass Lowell/Documents/GitHub/Spring-25---Network-Design/completion_time_vs_window_size.json"):
    if not os.path.exists(summary_file):
        print(f"Error: Summary file '{summary_file}' not found. Please run batch_runner.py first.")
        return

    with open(summary_file, "r") as f:
        results = json.load(f)

    if not results:
        print("No data found in results file.")
        return

    window_sizes = [x[0] for x in results]
    completion_times = [x[1] if x[1] is not None else 999.0 for x in results]  # Fill missing

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
