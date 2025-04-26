import json
import time
import threading
import os
import traceback
import socket
from tcp_connection import SimpleTCPConnection
from network_simulator import NetworkSimulator

print(f"DEBUG: Current working directory: {os.getcwd()}")

def run_simulation(loss_rate, delay_rate, max_delay):
    """Run a single simulation with the given parameters."""
    simulator = NetworkSimulator(
        loss_rate=loss_rate,        # <-- from function argument
        delay_rate=delay_rate,      # <-- from function argument
        max_delay=max_delay,        # <-- from function argument
        burst_loss_rate=0.3,        # Increased burst loss rate
        burst_length=5              # Increased burst length
    )

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 54321))
    server_socket.listen(1)

    server_conn = None
    client_conn = None

    try:
        # Server accept thread
        def accept_server():
            nonlocal server_conn
            conn, addr = server_socket.accept()
            server_conn = SimpleTCPConnection()
            server_conn.simulator = simulator
            server_conn.sock = conn
            server_conn.is_running = True
            server_conn.state = "ESTABLISHED"
            server_conn.remote_address = addr
            print(f"Server: Accepted connection from {addr}")

            # Start a thread to receive and ACK data
            def server_receive_loop():
                try:
                    while True:
                        data = conn.recv(2048)
                        if not data:
                            break
                        server_conn.handle_segment(data)  # Process incoming data and send ACKs
                except Exception as e:
                    print(f"Server receive error: {e}")

            threading.Thread(target=server_receive_loop, daemon=True).start()

        accept_thread = threading.Thread(target=accept_server)
        accept_thread.start()

        # Create client
        client_conn = SimpleTCPConnection()
        client_conn.simulator = simulator
        client_conn.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_conn.sock.connect(("127.0.0.1", 54321))
        client_conn.remote_address = ("127.0.0.1", 54321)
        client_conn.is_running = True
        client_conn.state = "ESTABLISHED"

        accept_thread.join()

        print("Connection established.")

        # Start sending data
        start_time = time.time()

        data = b"A" * 500_000  # Sending 500 KB of data
        print("DEBUG: Calling client.send()")
        client_conn.send(data)
        print("DEBUG: Returned from client.send()")

        # Wait for congestion control to take effect
        sleep_time = max(10, len(data) / 5000)  # At least 10 seconds, or based on data volume
        print(f"DEBUG: Sleeping for {sleep_time:.2f} seconds to allow transfer completion.")
        time.sleep(sleep_time)

        end_time = time.time()

        client_conn.close()
        server_socket.close()

    except Exception as e:
        print(f"ERROR: Unhandled exception: {e}")
        traceback.print_exc()

    finally:
        print("--- Entering FINALLY block ---")
        try:
            duration = (end_time - start_time) if client_conn else None
        except:
            duration = None

        # Save all logs (RTT, CWND, RTO) in the JSON output
        simulation_log = {
            "loss_rate": loss_rate,
            "delay_rate": delay_rate,
            "max_delay": max_delay,
            "completion_time": duration,
            "status": "success" if duration else "failure",
            "cwnd_log": getattr(client_conn, "cwnd_log", []),  # Save cwnd_log
            "rtt_log": getattr(client_conn, "rtt_log", []),    # Save rtt_log (optional)
            "rto_log": getattr(client_conn, "rto_log", [])     # Save rto_log (optional)
        }

        output_file = f"simulation_loss_{loss_rate}_delay_{delay_rate}.json"
        try:
            with open(output_file, "w") as f:
                json.dump(simulation_log, f, indent=4)
            print(f"INFO: Saved logs to {output_file}")
        except Exception as e:
            print(f"ERROR: Failed to save logs: {e}")

        # Update summary.json
        try:
            summary_file = "summary.json"
            if os.path.exists(summary_file):
                with open(summary_file, "r") as f:
                    summary = json.load(f)
            else:
                summary = []

            summary.append({
                "loss_rate": loss_rate,
                "delay_rate": delay_rate,
                "max_delay": max_delay,
                "completion_time": duration,
                "status": simulation_log["status"]
            })

            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=4)
            print("INFO: Updated summary.json")
        except Exception as e:
            print(f"ERROR: Failed updating summary: {e}")


def run_batch():
    """Run multiple simulations with different network conditions."""
    loss_rates = [0.0, 0.1, 0.3, 0.5]  # Add higher loss rates
    delay_rates = [0.0, 0.1, 0.5, 0.7]  # Add higher delay rates
    max_delays = [0.1, 0.5, 1.0]  # Increase max delays

    for loss in loss_rates:
        for delay in delay_rates:
            for max_delay in max_delays:
                print(f"\n===== Running simulation: loss={loss}, delay={delay}, max_delay={max_delay} =====")
                run_simulation(loss_rate=loss, delay_rate=delay, max_delay=max_delay)
                print(f"===== Completed simulation: loss={loss}, delay={delay}, max_delay={max_delay} =====\n")
                time.sleep(2)  # brief pause between runs

# ====== QUICK TEST RUN ======
if __name__ == "__main__":
    # Uncomment this to run just ONE simulation:
    # run_simulation(loss_rate=0.0, delay_rate=0.1, max_delay=0.5)

    # Comment out above line and instead run BATCH:
    run_batch()