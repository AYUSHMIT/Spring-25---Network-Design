import time
import threading
import matplotlib.pyplot as plt
from file_transfer import send_file, receive_file, create_udp_socket  # Import create_udp_socket

def update_fsm_state(state):
    print(f"FSM State: {state}")

def start_server(option, error_rate):
    def server_thread():
        server_error_rate = error_rate if option == 2 else 0.0  # Apply error rate only if option is 2
        receive_file(update_fsm_state, option, server_error_rate, sock=create_udp_socket(), listen_address=('localhost', 12345), save_path='received_image.jpg')
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
    return thread

def measure_completion_time(file_path, option, error_rate):
    server_thread = start_server(option, error_rate)
    time.sleep(1)  # Give the server some time to start
    client_error_rate = error_rate if option == 3 else 0.0  # Apply error rate only if option is 3
    start_time = time.time()
    send_file(file_path, update_fsm_state, option, client_error_rate)
    server_thread.join()  # Wait for the server to finish
    end_time = time.time()
    return end_time - start_time

def plot_performance():
    file_path = "C:/Users/Ayush_Pandey/Dev/Pandey_phase2/RDT/pandey/phase_2_JPG_500KB.jpg"  # Use a 500KB file for transmission
    error_rates = [i / 100 for i in range(0, 65, 5)]
    options = [1, 2, 3]
    completion_times = {option: [] for option in options}

    for option in options:
        for error_rate in error_rates:
            times = [measure_completion_time(file_path, option, error_rate) for _ in range(10)]  # Send 10 images per error point
            avg_time = sum(times) / len(times)
            completion_times[option].append(avg_time)
            print(f"Option {option}, Error Rate {error_rate}: {avg_time} seconds")

    for option in options:
        plt.plot(error_rates, completion_times[option], label=f"Option {option}")

    plt.xlabel("Error Rate")
    plt.ylabel("Completion Time (s)")
    plt.title("Completion Time vs Error Rate")
    plt.legend()
    plt.savefig("performance_plot.png")  # Save the plot to a file
    plt.show()

# Run the performance test and plot the results
plot_performance()
