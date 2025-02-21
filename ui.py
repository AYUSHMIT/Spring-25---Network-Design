import tkinter as tk
from tkinter import filedialog
import socket
import threading

# Server details
SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345

# Packet size
PACKET_SIZE = 1024

def send_file():
    # Get the selected filename
    filename = filedialog.askopenfilename(
        initialdir="/",
        title="Select a File",
        filetypes=(("BMP files", "*.bmp"), ("all files", "*.*"))
    )

    if not filename:
        return

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Read the file data
    with open(filename, "rb") as f:
        file_data = f.read()

    # Calculate the number of packets
    num_packets = len(file_data) // PACKET_SIZE + (1 if len(file_data) % PACKET_SIZE else 0)

    # Convert num_packets to binary
    binary_num_packets = format(num_packets, 'b')

    # Send the binary number of packets to the server
    client_socket.sendto(binary_num_packets.encode(), (SERVER_IP, SERVER_PORT))

    # Send the file data in packets
    for i in range(num_packets):
        start = i * PACKET_SIZE
        end = min((i + 1) * PACKET_SIZE, len(file_data))
        packet = file_data[start:end]
        client_socket.sendto(packet, (SERVER_IP, SERVER_PORT))

    # Close the socket
    client_socket.close()

    # Display success message
    status_label.config(text="File sent successfully!")

def receive_file():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the specified port
    server_socket.bind(('', SERVER_PORT))

    # Continuously listen for incoming files
    while True:
        # Receive the binary number of packets from the client
        binary_num_packets, client_address = server_socket.recvfrom(1024)

        # Convert binary to integer
        num_packets = int(binary_num_packets.decode(), 2)

        # Receive the file data in packets
        file_data = b""
        for i in range(num_packets):
            packet, client_address = server_socket.recvfrom(1024)
            file_data += packet

        # Save the received file data
        with open("received_image.bmp", "wb") as f:
            f.write(file_data)

        # Display success message
        status_label.config(text="File received successfully!")

# Create the main window
window = tk.Tk()
window.title("UDP File Transfer")

# Create a button to select and send the file
send_button = tk.Button(window, text="Send File", command=send_file)
send_button.pack(pady=20)

# Create a button to start receiving the file
receive_button = tk.Button(window, text="Receive File", command=lambda: threading.Thread(target=receive_file, daemon=True).start())
receive_button.pack()

# Create a label to display the status
status_label = tk.Label(window, text="")
status_label.pack()

# Run the main loop
window.mainloop()