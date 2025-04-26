import json
import time
import threading
from client import TCPClient
from server import TCPServer
from network_simulator import NetworkSimulator
import os
import traceback

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
            time.sleep(0.1)  # Check every 100ms
        print("Connection established.")

        # Record the start time
        start_time = time.time()

        # Now send data
        print("DEBUG: Calling client.send_data()")
        client.send_data(b"A" * 10240)  # Send 10 KB of data
        print("DEBUG: Returned from client.send_data()")

        # Wait for the transfer to complete with a timeout
        print("DEBUG: Entering completion check loop...")
        timeout_duration = 120  # Timeout in seconds (Increased from 30)
        completion_check_start_time = time.time()

        while not client.connection.is_transfer_complete():
            time.sleep(0.1)
            elapsed_time = time.time() - completion_check_start_time
            if elapsed_time > timeout_duration:
                print(f"ERROR: Simulation timed out after {timeout_duration} seconds waiting for completion.")
                # Optional: Add more debug info here about the state
                print(f"DEBUG: Client state: {client.connection.state}, Send Base: {client.connection.send_base}, Unacked Segments: {len(client.connection.unacked_segments)}")
                break  # Exit the loop if it times out
        else:
            print("DEBUG: Exited completion check loop normally.")
            end_time = time.time()

        # Wait for threads to finish
        print("DEBUG: Attempting to join client_thread...")
        if client_thread:
            client_thread.join()
        print("DEBUG: client_thread joined.")
        print("DEBUG: Attempting to join server_thread...")
        if server_thread:
            server_thread.join()
        print("DEBUG: server_thread joined.")

        # Now close the sockets
        print("DEBUG: Attempting client.close()...")
        if client:
            client.close()
        print("DEBUG: client closed.")
        print("DEBUG: Attempting server.close()...")
        if server:
            server.close()
        print("DEBUG: server closed.")

    except Exception as e:
        print(f"ERROR: Unhandled exception during simulation run: {e}")
        traceback.print_exc()

    finally:
        print("--- Entering FINALLY block ---")
        if client and hasattr(client, 'connection'):
            # --- Add Diagnostics Here ---
            print("-" * 20)
            print("DEBUG: Inspecting logs before saving JSON:")
            print(f"DEBUG: client.connection.cwnd_log length: {len(client.connection.cwnd_log)}")
            print(f"DEBUG: client.connection.rtt_log length: {len(client.connection.rtt_log)}")
            print(f"DEBUG: client.connection.rto_log length: {len(client.connection.rto_log)}")
            if client.connection.cwnd_log:
                print(f"DEBUG: First 5 cwnd entries: {client.connection.cwnd_log[:5]}")
            if client.connection.rtt_log:
                print(f"DEBUG: First 5 rtt entries: {client.connection.rtt_log[:5]}")
            if client.connection.rto_log:
                print(f"DEBUG: First 5 rto entries: {client.connection.rto_log[:5]}")
            print("-" * 20)
            # --- End Diagnostics ---

            # Collect logs
            data = {
                "cwnd_log": client.connection.cwnd_log,
                "rtt_log": client.connection.rtt_log,
                "rto_log": client.connection.rto_log,
                "completion_time": end_time - start_time if 'end_time' in locals() else None,
            }
            print(f"DEBUG: Data dictionary prepared for JSON: {str(data)[:500]}...")

            # Save logs to a file
            output_file = f"simulation_loss_{loss_rate}_delay_{delay_rate}.json"
            print(f"DEBUG: Saving logs to {output_file}")
            try:
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"DEBUG: Logs saved successfully to {output_file}")
            except Exception as e:
                print(f"ERROR: Failed to save JSON to {output_file}: {e}")
                traceback.print_exc()
        else:
            print("ERROR: Client object or connection not available in finally block. Cannot save logs.")

# Run simulations with varying loss rates
for loss_rate in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    run_simulation(loss_rate=loss_rate, delay_rate=0.1, max_delay=0.5)