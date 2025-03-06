import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random
import time

# -------------------------------------------------------------------
# Define the sender and receiver finite state machines as lists.
# These lists represent the state labels that will be drawn.
# -------------------------------------------------------------------
sender_states = [
    "STATE_0: Wait from call 0",
    "STATE_1: Wait for ACK 0",
    "STATE_2: Wait from call 1",
    "STATE_3: Wait for ACK 1",
]

receiver_states = [
    "STATE_0: Wait for 0",
    "STATE_1: Wait for 1",
]


# -------------------------------------------------------------------
# The main application class encapsulating the GUI and simulation logic.
# -------------------------------------------------------------------
class DataTransferApp:
    def __init__(self, root):
        # Set up the main window title and size
        self.root = root
        self.root.title("Data Transfer Visualization & FSM")
        self.root.geometry("1100x800")

        # Simulation parameters:
        self.error_probability = 0.2  # 20% chance for a packet to be simulated as "corrupt"
        self.packets_sent = 0         # Count of successfully transmitted packets
        self.total_packets = 10       # Total number of packets to simulate transfer
        self.sender_state = 0         # Current sender FSM state index
        self.receiver_state = 0       # Current receiver FSM state index
        self.running = False          # Flag indicating whether the transfer simulation is running

        # Set the image file path for the simulation.
        # You must have an image at this path or change this path accordingly.
        self.image_path = "input_file.bmp"

        # Build and arrange the GUI frames and widgets.
        self.create_frames()

    # -------------------------------------------------------------------
    # Set up the layout frames for FSM visualization and data transfer.
    # -------------------------------------------------------------------
    def create_frames(self):
        # --- Top frame holds the FSM displays ---
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill="both", expand=True)

        # Sender FSM frame and canvas
        sender_frame = tk.LabelFrame(top_frame, text="Sender FSM", padx=10, pady=10)
        sender_frame.pack(side="left", padx=10, pady=10)
        self.sender_fsm_canvas = tk.Canvas(sender_frame, width=700, height=150, bg="white")
        self.sender_fsm_canvas.pack()

        # Receiver FSM frame and canvas
        receiver_frame = tk.LabelFrame(top_frame, text="Receiver FSM", padx=10, pady=10)
        receiver_frame.pack(side="right", padx=10, pady=10)
        self.receiver_fsm_canvas = tk.Canvas(receiver_frame, width=300, height=150, bg="white")
        self.receiver_fsm_canvas.pack()

        # --- Middle frame holds the image transfer visualization ---
        middle_frame = tk.LabelFrame(self.root, text="Data Transfer Visualization", padx=10, pady=10)
        middle_frame.pack(pady=10, fill="both", expand=True)
        self.data_canvas = tk.Canvas(middle_frame, width=800, height=400, bg="gray")
        self.data_canvas.pack()

        # --- Bottom frame holds control buttons and log display ---
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10, fill="x")

        # Label to display current packet status
        self.packet_info_label = tk.Label(bottom_frame, text="Packet Info: ", font=("Arial", 12))
        self.packet_info_label.pack(side="left", padx=10)

        # Control Buttons for starting, stopping, and resetting the simulation
        start_btn = ttk.Button(bottom_frame, text="Start Transfer", command=self.start_transfer)
        start_btn.pack(side="left", padx=5)
        stop_btn = ttk.Button(bottom_frame, text="Stop Transfer", command=self.stop_transfer)
        stop_btn.pack(side="left", padx=5)
        reset_btn = ttk.Button(bottom_frame, text="Reset", command=self.reset_transfer)
        reset_btn.pack(side="left", padx=5)

        # A text widget to show a log of events and errors.
        self.log_text = tk.Text(bottom_frame, height=4, width=70, font=("Arial", 10))
        self.log_text.pack(side="left", padx=10)
        self.log("Application started.")

    # -------------------------------------------------------------------
    # Utility function to log messages with timestamps to the log_text widget.
    # -------------------------------------------------------------------
    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S] ")
        self.log_text.insert("end", f"{timestamp}{message}\n")
        self.log_text.see("end")  # Auto-scroll to the latest log entry

    # -------------------------------------------------------------------
    # Draw the FSM for a given canvas.
    # For each state, a rectangle (box) is drawn with the state label, and an arrow indicates transitions.
    # The currently active state is highlighted.
    # -------------------------------------------------------------------
    def draw_fsm(self, canvas, states, current_index):
        canvas.delete("all")  # Clear previous drawings
        box_width = 120
        box_height = 50
        gap = 20
        x_offset = 20
        y_offset = 40

        # Loop through each state and draw its box
        for i, state in enumerate(states):
            x1 = x_offset + i * (box_width + gap)
            y1 = y_offset
            x2 = x1 + box_width
            y2 = y1 + box_height

            # Highlight the current state with a different fill color
            fill_color = "lightgreen" if i == current_index else "white"
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="black", width=2)
            canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                               text=state, font=("Arial", 10), width=box_width-10)
            # Draw an arrow to the next state if this is not the last state
            if i < len(states) - 1:
                arrow_x = x2 + gap / 2
                arrow_y = (y1 + y2) / 2
                canvas.create_line(x2, arrow_y, arrow_x, arrow_y, arrow=tk.LAST, width=2)

    # -------------------------------------------------------------------
    # Update both sender and receiver FSM displays.
    # -------------------------------------------------------------------
    def update_fsm_displays(self):
        self.draw_fsm(self.sender_fsm_canvas, sender_states, self.sender_state)
        self.draw_fsm(self.receiver_fsm_canvas, receiver_states, self.receiver_state)

    # -------------------------------------------------------------------
    # Updates the data transfer canvas by progressively revealing more of the image.
    # The image is progressively cropped based on the number of packets successfully sent.
    # -------------------------------------------------------------------
    def update_image(self, packets_sent, total_packets):
        try:
            # Open the image using PIL
            img = Image.open(self.image_path)
            width, height = img.size
            # Calculate the height of the image portion to display based on transfer progress
            progress_height = int((packets_sent / total_packets) * height)
            if progress_height <= 0:  # Ensure at least 1 pixel is shown
                progress_height = 1
            # Crop the image from the top to the calculated progress height
            cropped_img = img.crop((0, 0, width, progress_height))
            # Convert the cropped image to a Tkinter-compatible PhotoImage
            img_tk = ImageTk.PhotoImage(cropped_img)
            self.data_canvas.delete("all")   # Clear the canvas
            # Place the image at the center of the data canvas
            self.data_canvas.create_image(400, 200, image=img_tk)
            self.data_canvas.image = img_tk  # Retain a reference to avoid garbage collection
        except Exception as e:
            self.log(f"Image update error: {e}")

    # -------------------------------------------------------------------
    # Start the simulated data transfer.
    # Sets the running flag and starts the transfer loop.
    # -------------------------------------------------------------------
    def start_transfer(self):
        self.running = True
        self.log("Transfer started.")
        self.transfer_loop()

    # -------------------------------------------------------------------
    # Stop (pause) the transfer, by clearing the running flag.
    # -------------------------------------------------------------------
    def stop_transfer(self):
        self.running = False
        self.log("Transfer paused.")

    # -------------------------------------------------------------------
    # Reset the simulation to initial state.
    # Clears the canvas, resets packet count and FSM indices.
    # -------------------------------------------------------------------
    def reset_transfer(self):
        self.running = False
        self.packets_sent = 0
        self.sender_state = 0
        self.receiver_state = 0
        self.data_canvas.delete("all")
        self.update_fsm_displays()
        self.packet_info_label.config(text="Packet Info: Reset")
        self.log("Transfer reset.")

    # -------------------------------------------------------------------
    # The main loop to simulate packet transfer.
    # This method updates the FSM, simulates a packet send (or error), and updates the image.
    # -------------------------------------------------------------------
    def transfer_loop(self):
        if self.running and self.packets_sent < self.total_packets:
            # Simulate a potential error based on a defined probability
            if random.random() < self.error_probability:
                # Simulated error: Do not increment the packet count and log a retransmission.
                self.log("Error: Packet corruption detected. Retransmitting...")
                self.packet_info_label.config(
                    text=f"Packet {self.packets_sent+1}/{self.total_packets} - ERROR, retransmission"
                )
                # In case of error, we do not advance the FSM states.
            else:
                # Successful transmission: increment the packet count.
                self.packets_sent += 1
                # Advance the sender FSM (cycle through 4 states) and receiver FSM (cycle through 2 states).
                self.sender_state = (self.sender_state + 1) % len(sender_states)
                self.receiver_state = (self.receiver_state + 1) % len(receiver_states)
                self.log(f"Packet {self.packets_sent}/{self.total_packets} transmitted successfully.")
                self.packet_info_label.config(
                    text=f"Packet {self.packets_sent}/{self.total_packets} transmitted"
                )
                # Update the image progress based on number of packets successfully transmitted.
                self.update_image(self.packets_sent, self.total_packets)
            
            # Refresh the FSM displays after state change or error.
            self.update_fsm_displays()
            # Schedule the next packet update after a 1-second delay.
            self.root.after(1000, self.transfer_loop)
        elif self.packets_sent >= self.total_packets:
            # Once all packets have been sent, log that the transfer is complete.
            self.log("Transfer complete.")
            self.packet_info_label.config(text="Transfer Complete")
            self.running = False


# -------------------------------------------------------------------
# Main entry point for the application.
# Create the Tkinter window and start the main loop.
# -------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = DataTransferApp(root)
    root.mainloop()
