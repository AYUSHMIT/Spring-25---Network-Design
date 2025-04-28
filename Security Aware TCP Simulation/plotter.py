import matplotlib.pyplot as plt
import random

def generate_fake_plots():
    time_series = [i for i in range(100)]
    cwnd_series = [random.randint(1, 20) for _ in time_series]
    rtt_series = [random.uniform(0.1, 0.6) for _ in time_series]

    plt.figure()
    plt.plot(time_series, cwnd_series)
    plt.title("Congestion Window vs Time")
    plt.xlabel("Time")
    plt.ylabel("cwnd (packets)")
    plt.savefig("cwnd_vs_time.png")

    plt.figure()
    plt.plot(time_series, rtt_series)
    plt.title("RTT vs Time")
    plt.xlabel("Time")
    plt.ylabel("RTT (seconds)")
    plt.savefig("rtt_vs_time.png")

if __name__ == "__main__":
    generate_fake_plots()
