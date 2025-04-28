import simulation_runner
import time
import json

def run_batch_timeout():
    """
    Run simulations with different timeout values and save the results.
    This function tests how varying timeout values affect the completion time of simulations.
    """
    # List of timeout values to test (in seconds)
    timeout_values = [0.05, 0.1, 0.3]  # Timeout values in seconds
    # Fixed parameters for the simulation
    loss_rate = 0.0  # No packet loss
    delay_rate = 0.0  # No delay rate
    max_delay = 0.0  # No maximum delay

    # List to store results of the simulations
    results = []

    print("\n=== Running batch simulations for timeout values ===")

    # Iterate over each timeout value and run the simulation
    for timeout in timeout_values:
        try:
            print(f"\n🚀 Running simulation with timeout={timeout*1000:.1f} ms")
            # Run the simulation with the current timeout value
            completion_time = simulation_runner.run_simulation(
                loss_rate=loss_rate, delay_rate=delay_rate, max_delay=max_delay, timeout=timeout
            )
            # Check if the simulation completed successfully
            if completion_time is not None:
                print(f"✅ Completed in {completion_time:.2f} seconds.")
            else:
                print(f"❌ Simulation failed for timeout={timeout}")
            # Append the results (timeout, completion_time) to the results list
            results.append((timeout, completion_time))
        except Exception as e:
            # Handle any exceptions during the simulation
            print(f"❌ ERROR: Simulation failed for timeout={timeout}: {e}")
            results.append((timeout, None))

    # Save the results to a JSON file
    with open("completion_time_vs_timeout.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\n📄 Saved results to completion_time_vs_timeout.json")


def run_batch_window_size():
    """
    Run simulations with different window sizes and save the results.
    This function tests how varying window sizes affect the completion time of simulations.
    """
    # List of window sizes to test
    window_sizes = [1, 10, 50]  # Window sizes
    # Fixed parameters for the simulation
    loss_rate = 0.1  # 10% packet loss
    delay_rate = 0.0  # No delay rate
    max_delay = 0.0  # No maximum delay

    # List to store results of the simulations
    results = []

    print("\n=== Running batch simulations for window sizes ===")

    # Iterate over each window size and run the simulation
    for window_size in window_sizes:
        try:
            print(f"\n🚀 Running simulation with window_size={window_size}")
            # Run the simulation with the current window size
            completion_time = simulation_runner.run_simulation(
                loss_rate=loss_rate, delay_rate=delay_rate, max_delay=max_delay, window_size=window_size
            )
            # Check if the simulation completed successfully
            if completion_time is not None:
                print(f"✅ Completed in {completion_time:.2f} seconds.")
            else:
                print(f"❌ Simulation failed for window_size={window_size}")
            # Append the results (window_size, completion_time) to the results list
            results.append((window_size, completion_time))
        except Exception as e:
            # Handle any exceptions during the simulation
            print(f"❌ ERROR: Simulation failed for window_size={window_size}: {e}")
            results.append((window_size, None))

    # Save the results to a JSON file
    with open("completion_time_vs_window_size.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\n📄 Saved results to completion_time_vs_window_size.json")


if __name__ == "__main__":
    # Run batch simulations for timeout values
    run_batch_timeout()
    # Run batch simulations for window sizes
    run_batch_window_size()