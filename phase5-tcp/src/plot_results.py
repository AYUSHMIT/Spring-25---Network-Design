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

def plot_simulation(filename, data):
    """Plot cwnd, rtt, and rto for a single simulation."""
    base_name = filename.replace('.json', '')
    save_folder = os.path.join(RESULTS_DIR, "plots")
    os.makedirs(save_folder, exist_ok=True)

    # Extract time and cwnd values from cwnd_log
    cwnd_log = data.get('cwnd_log', [])
    time_cwnd = [entry['time'] for entry in cwnd_log]
    cwnd_values = [entry['cwnd'] for entry in cwnd_log]

    # Extract RTT and RTO logs (if available)
    rtt_log = data.get('rtt_log', [])
    time_rtt = list(range(len(rtt_log)))
    rto_log = data.get('rto_log', [])
    time_rto = list(range(len(rto_log)))

    # Plot CWND Evolution
    plt.figure()
    plt.plot(time_cwnd, cwnd_values)
    plt.title(f"CWND Evolution: {base_name}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("CWND (segments)")
    plt.grid(True)
    plt.savefig(os.path.join(save_folder, f"{base_name}_cwnd.png"))
    plt.close()

    # Plot RTT Evolution
    plt.figure()
    plt.plot(time_rtt, rtt_log)
    plt.title(f"RTT Evolution: {base_name}")
    plt.xlabel("Time (arbitrary units)")
    plt.ylabel("RTT (seconds)")
    plt.grid(True)
    plt.savefig(os.path.join(save_folder, f"{base_name}_rtt.png"))
    plt.close()

    # Plot RTO Evolution
    plt.figure()
    plt.plot(time_rto, rto_log)
    plt.title(f"RTO Evolution: {base_name}")
    plt.xlabel("Time (arbitrary units)")
    plt.ylabel("RTO (seconds)")
    plt.grid(True)
    plt.savefig(os.path.join(save_folder, f"{base_name}_rto.png"))
    plt.close()

if __name__ == "__main__":
    simulations = load_simulation_data()
    if not simulations:
        print("No simulation JSON files found.")
    else:
        print(f"Found {len(simulations)} simulations. Plotting...")
        for filename, data in simulations:
            print(f"Plotting {filename}...")
            plot_simulation(filename, data)
        print("✅ All plots saved in the 'plots/' folder!")
