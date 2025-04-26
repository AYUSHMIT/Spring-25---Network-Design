import json
import os
import matplotlib.pyplot as plt

# Go 2 levels up from src/ into main project folder
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def load_simulation_data():
    """Load all simulation results."""
    simulation_data = []
    for filename in os.listdir(RESULTS_DIR):
        if filename.startswith("simulation_loss_") and filename.endswith(".json"):
            filepath = os.path.join(RESULTS_DIR, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
            simulation_data.append((filename, data))
    return simulation_data

def plot_rtt_comparison(simulations):
    """Plot RTT comparison across different simulations."""
    plt.figure(figsize=(12, 8))

    for filename, data in simulations:
        loss_delay_info = filename.replace("simulation_", "").replace(".json", "").replace("_", ", ")
        rtt_log = data.get('rtt_log', [])
        if rtt_log:
            plt.plot(range(len(rtt_log)), rtt_log, label=loss_delay_info)

    plt.title("Comparison of RTT Evolution Across Simulations")
    plt.xlabel("Time (arbitrary units)")
    plt.ylabel("RTT (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    save_folder = os.path.join(RESULTS_DIR, "plots")
    os.makedirs(save_folder, exist_ok=True)

    plt.savefig(os.path.join(save_folder, "comparison_rtt.png"))
    plt.close()
    print(f"✅ Saved RTT comparison plot at {os.path.join(save_folder, 'comparison_rtt.png')}")

if __name__ == "__main__":
    simulations = load_simulation_data()
    if not simulations:
        print("No simulation JSON files found.")
    else:
        print(f"Found {len(simulations)} simulations. Plotting RTT comparison...")
        plot_rtt_comparison(simulations)

