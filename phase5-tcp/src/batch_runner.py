import simulation_runner
import time
import json

def run_batch_timeout():
    """Run simulations with different timeout values and save results."""
    timeout_values = [0.05, 0.1, 0.3]  # Timeout values in seconds
    loss_rate = 0.0
    delay_rate = 0.0
    max_delay = 0.0

    results = []

    print("\n=== Running batch simulations for timeout values ===")

    for timeout in timeout_values:
        try:
            print(f"\n🚀 Running simulation with timeout={timeout*1000:.1f} ms")
            completion_time = simulation_runner.run_simulation(
                loss_rate=loss_rate, delay_rate=delay_rate, max_delay=max_delay, timeout=timeout
            )
            if completion_time is not None:
                print(f"✅ Completed in {completion_time:.2f} seconds.")
            else:
                print(f"❌ Simulation failed for timeout={timeout}")
            results.append((timeout, completion_time))
        except Exception as e:
            print(f"❌ ERROR: Simulation failed for timeout={timeout}: {e}")
            results.append((timeout, None))

    with open("completion_time_vs_timeout.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\n📄 Saved results to completion_time_vs_timeout.json")


def run_batch_window_size():
    """Run simulations with different window sizes and save results."""
    window_sizes = [1, 10, 50]  # Window sizes
    loss_rate = 0.1
    delay_rate = 0.0
    max_delay = 0.0

    results = []

    print("\n=== Running batch simulations for window sizes ===")

    for window_size in window_sizes:
        try:
            print(f"\n🚀 Running simulation with window_size={window_size}")
            completion_time = simulation_runner.run_simulation(
                loss_rate=loss_rate, delay_rate=delay_rate, max_delay=max_delay, window_size=window_size
            )
            if completion_time is not None:
                print(f"✅ Completed in {completion_time:.2f} seconds.")
            else:
                print(f"❌ Simulation failed for window_size={window_size}")
            results.append((window_size, completion_time))
        except Exception as e:
            print(f"❌ ERROR: Simulation failed for window_size={window_size}: {e}")
            results.append((window_size, None))

    with open("completion_time_vs_window_size.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\n📄 Saved results to completion_time_vs_window_size.json")


if __name__ == "__main__":
    run_batch_timeout()
    run_batch_window_size()
