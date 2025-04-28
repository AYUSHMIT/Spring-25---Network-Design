import threading
import random
import time
import matplotlib.pyplot as plt
from collections import deque

# Shared Channel (simulating CSMA/CA)
class Channel:
    """
    Represents a shared communication channel.
    Simulates CSMA/CA (Carrier Sense Multiple Access with Collision Avoidance).
    """
    def __init__(self):
        self.lock = threading.Lock()  # Lock to ensure thread-safe access
        self.active_senders = set()  # Set of active senders currently transmitting
    
    def sense(self):
        """
        Check if the channel is idle (no active senders).
        Returns True if the channel is idle, False otherwise.
        """
        return len(self.active_senders) == 0
    
    def transmit(self, flow_id):
        """
        Mark a flow as transmitting on the channel.
        """
        with self.lock:
            self.active_senders.add(flow_id)
    
    def end_transmit(self, flow_id):
        """
        Mark a flow as finished transmitting on the channel.
        """
        with self.lock:
            self.active_senders.discard(flow_id)
    
    def collision_detected(self):
        """
        Check if a collision has occurred (more than one active sender).
        Returns True if a collision is detected, False otherwise.
        """
        with self.lock:
            return len(self.active_senders) > 1

# TCP Sender (each flow/thread)
class TCPSender(threading.Thread):
    """
    Represents a TCP sender flow.
    Each flow runs as a separate thread and interacts with the shared channel.
    """
    def __init__(self, flow_id, channel, sim_duration, stats):
        threading.Thread.__init__(self)
        self.flow_id = flow_id  # Unique ID for the flow
        self.channel = channel  # Shared channel instance
        self.sim_duration = sim_duration  # Duration of the simulation
        self.start_time = time.time()  # Start time of the flow
        self.cwnd = 1  # Congestion window size
        self.ssthresh = 64  # Slow start threshold
        self.stats = stats  # Shared statistics dictionary
        self.running = True  # Flag to control the thread's execution
        self.rtt_samples = []  # List to store RTT samples for the flow
    
    def run(self):
        """
        Main execution loop for the TCP sender.
        Simulates packet transmission, collision handling, and congestion control.
        """
        next_packet_id = 0  # Packet sequence number
        while time.time() - self.start_time < self.sim_duration and self.running:
            packets_to_send = int(self.cwnd)  # Number of packets to send based on cwnd
            for _ in range(packets_to_send):
                if self.channel.sense():  # Check if the channel is idle
                    self.channel.transmit(self.flow_id)  # Start transmitting
                    transmission_delay = random.uniform(0.005, 0.01)  # Simulate transmission delay
                    time.sleep(transmission_delay)
                    
                    if self.channel.collision_detected():  # Check for collision
                        print(f"[Collision] Flow {self.flow_id} collision detected.")
                        self.handle_collision()  # Handle collision (congestion control)
                        self.stats['collisions'][self.flow_id] += 1
                    else:
                        print(f"[Success] Flow {self.flow_id} packet {next_packet_id} transmitted.")
                        self.cwnd_growth()  # Increase congestion window
                        self.stats['success'][self.flow_id] += 1
                        self.rtt_samples.append(transmission_delay * 2)  # Record RTT sample
                    
                    self.channel.end_transmit(self.flow_id)  # End transmission
                else:
                    self.random_backoff()  # Perform random backoff if the channel is busy
            time.sleep(0.01)  # Small delay to avoid busy looping
    
    def handle_collision(self):
        """
        Handle a collision by reducing the congestion window and updating the threshold.
        """
        self.ssthresh = max(self.cwnd // 2, 1)  # Update slow start threshold
        self.cwnd = 1  # Reset congestion window to 1 (TCP congestion response)
    
    def cwnd_growth(self):
        """
        Increase the congestion window based on the current phase (slow start or congestion avoidance).
        """
        if self.cwnd < self.ssthresh:
            self.cwnd += 1  # Slow start phase (exponential growth)
        else:
            self.cwnd += 1 / self.cwnd  # Congestion avoidance phase (linear growth)
    
    def random_backoff(self):
        """
        Perform a random backoff to avoid collisions.
        """
        backoff_time = random.uniform(0.02, 0.1)  # Random backoff time
        print(f"[Backoff] Flow {self.flow_id} backing off {backoff_time:.3f} sec")
        time.sleep(backoff_time)
    
    def stop(self):
        """
        Stop the thread by setting the running flag to False.
        """
        self.running = False

# Simulation Runner
def run_simulation(num_flows=3, duration=10):
    """
    Run the simulation with the specified number of flows and duration.
    Returns the statistics and flow objects.
    """
    channel = Channel()  # Create a shared channel
    stats = {
        'collisions': [0 for _ in range(num_flows)],  # Initialize collision counts
        'success': [0 for _ in range(num_flows)]  # Initialize success counts
    }
    flows = [TCPSender(flow_id=i, channel=channel, sim_duration=duration, stats=stats) for i in range(num_flows)]
    
    for f in flows:
        f.start()  # Start each flow thread
    
    time.sleep(duration)  # Run the simulation for the specified duration
    
    for f in flows:
        f.stop()  # Stop each flow thread
    for f in flows:
        f.join()  # Wait for all threads to finish
    
    return stats, flows

# Plotting Functions
def plot_results(stats, flows):
    """
    Plot the results of the simulation, including collisions, successes, and RTT samples.
    """
    num_flows = len(stats['collisions'])
    flow_ids = list(range(num_flows))
    
    # Plot collisions per flow
    plt.figure()
    plt.bar(flow_ids, stats['collisions'], label='Collisions per Flow')
    plt.title('Collisions per Flow')
    plt.xlabel('Flow ID')
    plt.ylabel('Collision Count')
    plt.legend()
    plt.show()

    # Plot successful packets per flow
    plt.figure()
    plt.bar(flow_ids, stats['success'], label='Successful Packets per Flow')
    plt.title('Successful Packets per Flow')
    plt.xlabel('Flow ID')
    plt.ylabel('Success Count')
    plt.legend()
    plt.show()

    # Plot RTT samples over time for each flow
    plt.figure()
    for flow in flows:
        times = [i for i in range(len(flow.rtt_samples))]
        plt.plot(times, flow.rtt_samples, label=f"Flow {flow.flow_id}")
    plt.title('Sampled RTT over Time')
    plt.xlabel('Packet Index')
    plt.ylabel('RTT (seconds)')
    plt.legend()
    plt.show()

# Main Program Entry
if __name__ == "__main__":
    stats, flows = run_simulation(num_flows=3, duration=15)  # Run the simulation
    plot_results(stats, flows)  # Plot the results