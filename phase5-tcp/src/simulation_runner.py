import json
import time
import threading
from client import TCPClient
from server import TCPServer
from network_simulator import NetworkSimulator

def start_server(simulator):
    server = TCPServer(server_ip="127.0.0.1", server_port=54321, simulator=simulator)
    server_thread = threading.Thread(target=server.receive_loop)
    server.is_running = True  # Add a flag to control the server loop
    server_thread.start()
    return server, server_thread

def run_simulation(loss_rate, delay_rate, max_delay):
    simulator = NetworkSimulator(loss_rate=loss_rate, delay_rate=delay_rate, max_delay=max_delay)

    # Start the server
    server, server_thread = start_server(simulator)

    # Set up the client
    client = TCPClient(server_ip="127.0.0.1", server_port=54321, simulator=simulator)
    client.is_running = True  # Add a flag to control the client loop

    # Connect the client to the server
    client.connect()

    # Start the client receive loop in a separate thread
    client_thread = threading.Thread(target=client.receive_loop)
    client_thread.start()

    # Start the file transfer
    start_time = time.time()
    client.send_data(b"Large file data...")

    # Wait for the transfer to complete
    while not client.connection.is_transfer_complete():
        time.sleep(0.1)

    end_time = time.time()

    # Signal threads to stop
    client.is_running = False
    server.is_running = False

    # Wait for threads to finish
    client_thread.join()
    server_thread.join()

    # Now close the sockets
    client.close()  # Assuming client.close also calls sock.close()
    server.close()

    # Collect logs
    data = {
        "cwnd_log": client.connection.cwnd_log,
        "rtt_log": client.connection.rtt_log,
        "rto_log": client.connection.rto_log,
        "completion_time": end_time - start_time,
    }

    # Save logs to a file
    with open(f"simulation_loss_{loss_rate}_delay_{delay_rate}.json", "w") as f:
        json.dump(data, f)

# Run simulations with varying loss rates
for loss_rate in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    run_simulation(loss_rate=loss_rate, delay_rate=0.1, max_delay=0.5)