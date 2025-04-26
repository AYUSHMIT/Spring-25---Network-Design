import simulation_runner

def run_batch():
    loss_rates = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    delay_rate = 0.1
    max_delay = 0.5

    for loss in loss_rates:
        print(f"\n=== Running simulation with loss_rate={loss*100}% ===")
        simulation_runner.run_simulation(loss_rate=loss, delay_rate=delay_rate, max_delay=max_delay)

if __name__ == "__main__":
    run_batch()
