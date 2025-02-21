import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
import matplotlib.pyplot as plt  # Import matplotlib.pyplot as plt
from file_transfer import receive_file
import client_phase_2

def start_receiver(option, error_rate):
    # Start the receive_file function in a separate thread
    threading.Thread(target=receive_file_with_status, args=(option, error_rate), daemon=True).start()

def receive_file_with_status(option, error_rate):
    try:
        update_fsm_state("Receiving file...")
        start_time = time.time()
        receive_file(update_fsm_state, option, error_rate)
        end_time = time.time()
        transfer_time = end_time - start_time
        status_label.config(text=f"File received successfully in {transfer_time:.2f} seconds!")
        display_image("received_image.jpg")
        window.after(0, plot_performance, transfer_time, "Receive")
    except Exception as e:
        status_label.config(text=f"Error receiving file: {e}")
        print(f"Error receiving file: {e}")

def send_file_with_status():
    file_path = filedialog.askopenfilename()
    if file_path:
        threading.Thread(target=send_file_thread, args=(file_path,), daemon=True).start()

def send_file_thread(file_path, retry_count=3):
    try:
        update_fsm_state("Sending file...")
        start_time = time.time()
        client_phase_2.send_file(file_path, update_fsm_state)
        end_time = time.time()
        transfer_time = end_time - start_time
        status_label.config(text=f"File sent successfully in {transfer_time:.2f} seconds!")
        display_image(file_path)
        window.after(0, plot_performance, transfer_time, "Send")
    except Exception as e:
        status_label.config(text=f"Error sending file: {e}")
        print(f"Error sending file: {e}")
        # Additional logging for debugging
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error sending file: {e}\n")
        # Attempt to reconnect or handle the error
        handle_connection_error(e, file_path, retry_count)

def handle_connection_error(error, file_path, retry_count):
    if isinstance(error, ConnectionResetError) and retry_count > 0:
        print("Connection was reset. Attempting to reconnect...")
        # Implement reconnection logic here
        # Retry sending the file after a short delay
        time.sleep(5)
        print(f"Retrying... {retry_count} attempts left.")
        send_file_thread(file_path, retry_count - 1)
    else:
        print(f"Unhandled error or no retries left: {error}")
        # Additional logging for debugging
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Unhandled error or no retries left: {error}\n")

def display_image(file_path):
    try:
        img = Image.open(file_path)
        img = img.resize((300, 300), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
        img = ImageTk.PhotoImage(img)
        image_label.config(image=img)
        image_label.image = img
    except Exception as e:
        messagebox.showerror("Error", f"Unable to display image: {e}")
        print(f"Unable to display image: {e}")

def update_fsm_state(state):
    fsm_label.config(text=f"FSM State: {state}")
    print(f"FSM State: {state}")

def plot_performance(transfer_time, operation):
    plt.figure()
    plt.bar(operation, transfer_time)
    plt.xlabel('Operation')
    plt.ylabel('Transfer Time (s)')
    plt.title('File Transfer Performance')
    plt.show()

# Create the main window
window = tk.Tk()
window.title("RDT 2.2 File Transfer")
window.geometry("600x600")

# Create a button to select and send the file
send_button = tk.Button(window, text="Send File", command=send_file_with_status, font=("Arial", 14))
send_button.pack(pady=20)

# Create a button to start receiving the file
receive_button = tk.Button(window, text="Receive File", command=lambda: start_receiver(1, 0.0), font=("Arial", 14))
receive_button.pack(pady=20)

# Create a label to display the status
status_label = tk.Label(window, text="", font=("Arial", 12))
status_label.pack(pady=10)

# Create a label to display the image
image_label = tk.Label(window)
image_label.pack(pady=10)

# Create a label to display the FSM state
fsm_label = tk.Label(window, text="FSM State: Idle", font=("Arial", 12))
fsm_label.pack(pady=10)

# Run the main loop
window.mainloop()