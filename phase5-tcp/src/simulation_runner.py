import socket
import time
import threading
import traceback
from network_simulator import NetworkSimulator
from tcp_connection import SimpleTCPConnection

def run_simulation(loss_rate, delay_rate, max_delay, timeout=None, window_size=None):
    """Run a single simulation with given network parameters."""
    simulator = NetworkSimulator(
        loss_rate=loss_rate,
        delay_rate=delay_rate,
        max_delay=max_delay,
        burst_loss_rate=0.0,
        burst_length=2
    )

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 54321))

    server_conn = None
    client_conn = None

    try:
        # --- Server receive thread ---
        def server_receive_loop():
            nonlocal server_conn
            server_conn = SimpleTCPConnection(sock=server_socket, addr=("127.0.0.1", 54321))
            server_conn.simulator = simulator
            server_conn.is_running = True
            server_conn.state = SimpleTCPConnection.ESTABLISHED
            print("Server: Ready to receive data.")

            while server_conn.is_running:
                try:
                    data, addr = server_socket.recvfrom(2048)
                    if not data:
                        break
                    server_conn.remote_address = addr
                    server_conn.handle_segment(data)
                except Exception as e:
                    print(f"CRITICAL ERROR in server_receive_loop: {e}")
                    traceback.print_exc()
                    break

        server_thread = threading.Thread(target=server_receive_loop, daemon=True)
        server_thread.start()

        # --- Client setup ---
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.bind(("127.0.0.1", 0))  # Bind to random port

        client_conn = SimpleTCPConnection(sock=client_socket, addr=("127.0.0.1", 54321))
        client_conn.simulator = simulator
        client_conn.is_running = True
        client_conn.state = SimpleTCPConnection.ESTABLISHED

        if timeout is not None:
            print(f"INFO: Setting initial RTO for client to {timeout} seconds")
            client_conn.rto = timeout

        if window_size is not None:
            print(f"INFO: Setting initial CWND for client to {window_size}")
            client_conn.congestion_control.congestion_window = float(window_size)

        # --- Client receive thread ---
        def client_receive_loop():
            print("DEBUG: client_receive_loop started!")
            while client_conn.is_running:
                try:
                    data, addr = client_conn.sock.recvfrom(2048)
                    if not data:
                        break
                    client_conn.handle_segment(data)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"CRITICAL ERROR in client_receive_loop: {e}")
                    traceback.print_exc()
                    break

        client_thread = threading.Thread(target=client_receive_loop, daemon=True)
        client_thread.start()

        # --- Start transmission ---
        print("Connection established.")
        start_time = time.time()

        data = b"A" * 500_000  # Send 500 KB
        print("DEBUG: Calling client.send()")
        client_conn.send(data)
        print("DEBUG: Returned from client.send()")

        # --- Wait for transfer completion ---
        simulation_timeout = 30  # Max wait seconds
        wait_start = time.time()

        while True:
            if client_conn.is_transfer_complete():
                print("✅ DEBUG: Transfer complete!")
                break
            if time.time() - wait_start > simulation_timeout:
                print("🚨 HARD TIMEOUT: Force-ending simulation.")
                break
            time.sleep(0.5)

        end_time = time.time()

        # Clean close
        client_conn.close()
        if server_conn:
            server_conn.close()
        if server_socket:
            server_socket.close()

        return end_time - start_time

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return None

    finally:
        print("--- Entering FINALLY block ---")
        if client_conn:
            client_conn.is_running = False
        if server_conn:
            server_conn.is_running = False

        if 'client_thread' in locals() and client_thread.is_alive():
            client_thread.join(timeout=1.0)
        if 'server_thread' in locals() and server_thread.is_alive():
            server_thread.join(timeout=1.0)

        if client_conn:
            try:
                client_conn.close()
            except:
                pass
        if server_socket:
            try:
                server_socket.close()
            except:
                pass
