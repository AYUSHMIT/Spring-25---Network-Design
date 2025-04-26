import json
import time
import threading
import os
import traceback
from client import TCPClient
from server import TCPServer
from network_simulator import NetworkSimulator

# Debug: Print the current working directory
print(f"DEBUG: Current working directory: {os.getcwd()}")

def start_server(simulator):
    """Start the server and its receive loop in a separate thread."""
    server = TCPServer(server_ip="127.0.0.1", server_port=54321, simulator=simulator)
    server.start()  # Bind the server socket to the IP and port
    server_thread = threading.Thread(target=server.receive_loop)
    server.is_running = True  # Add a flag to control the server loop
    server_thread.start()
    return server, server_thread

def run_simulation(loss_rate, delay_rate, max_delay):
    """Run a single simulation with the given parameters."""
    simulator = NetworkSimulator(loss_rate=loss_rate, delay_rate=delay_rate, max_delay=max_delay)
    server = client = client_thread = server_thread = None  # Initialize to None

    try:
        # Start the server
        server, server_thread = start_server(simulator)

        # Set up the client
        client = TCPClient(server_ip="127.0.0.1", server_port=54321, simulator=simulator)

        # Connect the client to the server
        client.connect()

        # Start the client receive loop in a separate thread
        client_thread = threading.Thread(target=client.receive_loop)
        client_thread.start()

        # Wait for the connection to establish
        print("Waiting for connection to establish...")
        while client.connection.state != 'ESTABLISHED':
            time.sleep(0.1)
        print("Connection established.")

        # Record the start time
        start_time = time.time()

        # Now send data (smaller size for faster runs)
        print("DEBUG: Calling client.send_data()")
        client.send_data(b"A" * 1024)  # Sending only 1KB instead of 10KB
        print("DEBUG: Returned from client.send_data()")

        # Wait for the transfer to complete with a timeout
        print("DEBUG: Entering completion check loop...")
        timeout_duration = 30  # 30 seconds timeout
        completion_check_start_time = time.time()
        timed_out = False

        while not client.connection.is_transfer_complete():
            time.sleep(0.1)
            elapsed_time = time.time() - completion_check_start_time
            if elapsed_time > timeout_duration:
                print(f"ERROR: Simulation timed out after {timeout_duration} seconds waiting for completion.")
                timed_out = True
                break

        if not timed_out:
            end_time = time.time()

        # No need to forcefully join stuck threads if timed out
        if client_thread and client_thread.is_alive():
            client_thread.join(timeout=2)
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=2)

        # Now close the sockets
        if client:
            client.close()
        if server:
            server.close()

    except Exception as e:
        print(f"ERROR: Unhandled exception during simulation run: {e}")
        traceback.print_exc()

    finally:
        print("--- Entering FINALLY block ---")
        data = {}
        try:
            if client and hasattr(client, 'connection'):
                connection = client.connection
                data = {
                    "cwnd_log": getattr(connection, "cwnd_log", []),
                    "rtt_log": getattr(connection, "rtt_log", []),
                    "rto_log": getattr(connection, "rto_log", []),
                    "completion_time": (end_time - start_time) if 'end_time' in locals() else None,
                    "status": "success" if not timed_out else "timeout"
                }
                print(f"DEBUG: Data dictionary prepared: {str(data)[:500]}...")
            else:
                print("WARNING: Client object or connection not available. Saving empty logs.")
                data = {
                    "cwnd_log": [],
                    "rtt_log": [],
                    "rto_log": [],
                    "completion_time": None,
                    "status": "no_connection"
                }
        except Exception as e:
            print(f"ERROR: Exception during preparing data dictionary: {e}")
            traceback.print_exc()

        # Always attempt to save
        output_file = f"simulation_loss_{loss_rate}_delay_{delay_rate}.json"
        absolute_path = os.path.abspath(output_file)
        try:
            with open(output_file, "w") as f:
                json.dump(data, f, indent=4)
            print(f"INFO: Logs saved successfully to {absolute_path}")
        except Exception as e:
            print(f"ERROR: Failed to save JSON to {absolute_path}: {e}")
            traceback.print_exc()

        # Append to summary.json
        try:
            summary_file = "summary.json"
            if os.path.exists(summary_file):
                with open(summary_file, "r") as f:
                    summary_data = json.load(f)
            else:
                summary_data = []

            summary_entry = {
                "loss_rate": loss_rate,
                "delay_rate": delay_rate,
                "max_delay": max_delay,
                "completion_time": data.get("completion_time"),
                "status": data.get("status"),
            }
            summary_data.append(summary_entry)

            with open(summary_file, "w") as f:
                json.dump(summary_data, f, indent=4)
            print(f"INFO: Appended result to summary.json")
        except Exception as e:
            print(f"ERROR: Failed to update summary.json: {e}")
            traceback.print_exc()

# === Run a Single Simulation Example ===
run_simulation(loss_rate=0.0, delay_rate=0.1, max_delay=0.5)