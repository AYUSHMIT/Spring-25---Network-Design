# -------------------------------------------------------------------
'''Python libraries begins'''
# -------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import random
import queue
from socket import *  # Import socket library for network communication
from enum import Enum  # Import Enum for defining states
import struct  # Import struct for working with binary data

# -------------------------------------------------------------------
'''End python libraries'''
# -------------------------------------------------------------------

# -------------------------------------------------------------------
'''Constants definitions begins'''
# -------------------------------------------------------------------
CHECKSUM = struct.calcsize("I")     # I = Interger = 4 Bytes
SEQ_NUM = struct.calcsize("B")      # B =  1 Byte
HEADER_SIZE = CHECKSUM + SEQ_NUM

FILE_PATH = "input_file.bmp"  # File path for the input file to be sent

PACKET_SIZE = 1024  # Define the size of each data packet in bytes

# Sender details
HOST_A_PORT = 13000  # Port number to bind the sender's UDP socket

# Receiver details
HOST_B_ADDRESS = 'localhost'  # Receiver's address (localhost for local testing)
HOST_B_PORT = 12000  # Receiver's port number

# -------------------------------------------------------------------
'''Define FSM state labels for sender and receiver.'''
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

######################################################################
'''
class state(Enum):
    # Define states for the state machine
    STATE_0 = "STATE_0: Wait for 0"  # Waiting for packets with sequence number 0
    STATE_1 = "STATE_1: Wait for 1"  # Waiting for packets with sequence number 1

# State transition dictionary for handling state transitions
state_transitions = {
    state.STATE_0.value: {  # Transitions for STATE_0
        'NEXT': state.STATE_1.value,  # Transition to STATE_1
        'STAY': state.STATE_0.value   # Stay in STATE_0
    },
    state.STATE_1.value: {  # Transitions for STATE_1
        'NEXT': state.STATE_0.value,  # Transition to STATE_0
        'STAY': state.STATE_1.value   # Stay in STATE_1
    }
}
'''

'''
class state(Enum):
    # Enum class to define sender's states in the state machine
    STATE_0 = "Current State: Wait from call 0 from above"  # Initial state, waiting for data
    STATE_1 = "Current State: Wait for ACK 0"  # Waiting for acknowledgment (ACK) for sequence 0
    STATE_2 = "Current State: Wait from call 1 from above"  # Waiting to send data for sequence 1
    STATE_3 = "Current State: Wait for ACK 1"  # Waiting for ACK for sequence 1

# State transition dictionary for handling state transitions
state_transitions = {
    state.STATE_0.name: {               # Define transitions for 'STATE_0'
        'NEXT': state.STATE_1.name,     # If input is 'NEXT', transition to 'STATE_1'
        'STAY': state.STATE_0.name      # If input is 'STAY', remain in 'STATE_0'
    },
    state.STATE_1.name: {               # Define transitions for 'STATE_1'
        'NEXT': state.STATE_2.name,     # If input is 'NEXT', transition to 'STATE_2'
        'STAY': state.STATE_1.name      # If input is 'STAY', remain in 'STATE_1'
    },
    state.STATE_2.name: {               # Define transitions for 'STATE_2'
        'NEXT': state.STATE_3.name,     # If input is 'NEXT', transition to 'STATE_3'
        'STAY': state.STATE_2.name      # If input is 'STAY', remain in 'STATE_2'
    },
    state.STATE_3.name: {               # Define transitions for 'STATE_3'
        'NEXT': state.STATE_0.name,     # If input is 'NEXT', transition to 'STATE_0'
        'STAY': state.STATE_3.name      # If input is 'STAY', remain in 'STATE_3'
    }
}
'''

'''
class PKT(Enum):
    CHECKSUM = 0
    SEQ_NUM  = 1
    DATA = 2
'''
#####################################################################
# -------------------------------------------------------------------
'''End of Constants Definitions'''
# -------------------------------------------------------------------

# -------------------------------------------------------------------
'''Receiver Function definitions begins'''
# -------------------------------------------------------------------
def calculate_checksum(seq_num, data): #expected_seq_num, ACK
    """
    Calculate the checksum using XOR operation.
    
    Args:
        seq_num (int): Sequence number (0 or 1).
        data (bytes): Data or acknowledgment bytes.
    
    Returns:
        int: Computed checksum.
    """
    checksum = seq_num  # Start with the sequence number
    for byte in data:
        checksum ^= byte  # XOR each byte in the data
    return checksum

def extract(packet):
    """
    Extract checksum, sequence number, and data from the packet.
    
    Args:
        packet (bytes): The received packet.
    
    Returns:
        tuple: (checksum, sequence number, data)
    """
    header_format = "I B"  # Format: unsigned int for checksum, unsigned char for seq_num
    header_size = struct.calcsize(header_format)
    checksum, seq_num = struct.unpack(header_format, packet[:header_size])  # Unpack header
    data = packet[header_size:]  # Extract data part of the packet
    return checksum, seq_num, data

def deliver_data(data, packet_num):
    """
    Deliver data to the application layer (e.g., save it as a file).
    
    Args:
        data (bytes): Data payload from the packet.
        packet_num (int): The packet number for file naming.
    """
    filename = f"Received_file{packet_num}.bmp"
    with open(filename, "wb") as file:
        file.write(data)
    print(f"File '{filename}' saved successfully.")

def transition(current_state, input_action):
    """
    Transition to the next state based on the current state and input.
    
    Args:
        current_state (int): Current FSM state index.
        input_action (str): Input action ('NEXT' to move forward).
    
    Returns:
        int: Next state index.
    """
    if input_action == "NEXT":
        return (current_state + 1) % len(receiver_states)  # Cyclic transition
    return current_state  # No transition if input is not 'NEXT'

def make_pkt(seq_num, ack_data):
    """
    Create a packet with checksum, sequence number, and acknowledgment data.
    
    Args:
        seq_num (int): Sequence number (0 or 1).
        ack_data (bytes): Acknowledgment payload (e.g., b"ACK").
    
    Returns:
        bytes: The constructed packet.
    """
    checksum = calculate_checksum(seq_num, ack_data)  # Calculate checksum
    header = struct.pack("I B", checksum, seq_num)  # Create packet header
    return header + ack_data  # Combine header and data

def is_final_packet(packet):
    """
    Check if the packet contains the EOF marker (end of file).
    
    Args:
        packet (bytes): The received packet.
    
    Returns:
        bool: True if it's the final packet, False otherwise.
    """
    header_size = struct.calcsize("I B")  # Header size from extract function
    EOF_MARKER = b'EOF'
    data = packet[header_size:]  # Extract the data portion
    return data.endswith(EOF_MARKER)  # Check if data ends with EOF marker
# -------------------------------------------------------------------
'''End of Receiver Function definitions'''
# -------------------------------------------------------------------
#####################################################################
# -------------------------------------------------------------------
'''Sender Function definitions begins'''
# -------------------------------------------------------------------
def get_user_choice():
    """
    Prompts the user for input (y/n) until valid input is provided.

    Returns:
    str: The validated user input ('y' or 'n').
    """
    try:
        answer = input("Send image, y/n?").strip().lower()  # Prompt user for input and normalize it
        if answer not in ['y', 'n']:
            # Raise error if input is invalid
            raise ValueError("Invalid input! Please enter 'y' or 'n'.")
        return answer  # Return valid input
    except ValueError as ve:
        print(ve)  # Print error message for invalid input

def get_file_data(file_path=FILE_PATH, packet_size=PACKET_SIZE):
    data = []
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            for i in range(0, len(file_data), packet_size):
                chunk = file_data[i:i + packet_size]
                if i + packet_size >= len(file_data):  # Final packet
                    chunk += b'EOF'  # Append "EOF" marker to the final packet
                data.append(chunk)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

def calculate_checksum(seq_num, data):
    """
    Computes the checksum using XOR operation.

    Args:
    seq_num (int): Sequence number of the packet.
    data (bytes): Data portion of the packet.

    Returns:
    int: The calculated checksum value.
    """
    checksum = seq_num  # Start with the sequence number
    for byte in data:
        # XOR the sequence number with each byte in the data
        checksum ^= byte
    return checksum  # Return the final checksum value

def rdt_send(socket, host_address, data, seq_num):
    """
    Sends a packet reliably using the sequence number and checksum.

    Args:
    data (bytes): The data portion of the packet to be sent.
    seq_num (int): The sequence number of the packet (0 or 1).
    """
    sndpkt = make_pkt(seq_num, data)  # Create a complete packet
    socket.sendto(sndpkt, (host_address, HOST_B_PORT))  # Send the packet via UDP to the receiver

''' Note: Not used for now.
def transition(state, input):
    """
    Handle state transitions based on the current state and input.

    Args:
        state (str): Current state name.
        input (str): Transition input ('NEXT' or 'STAY').

    Returns:
        str: Next state name.
    """
    return state_transitions[state].get(input, state)  # Get the next state or remain in the current state
'''

# -------------------------------------------------------------------
'''End of Sender Function definitions'''
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# A shared queue to simulate packet transfer from sender to receiver.
# In a real application this might be replaced by actual socket communication.
# -------------------------------------------------------------------
packet_queue = queue.Queue()


# -------------------------------------------------------------------
# The GUI Application class. This class constructs the GUI
# and provides thread–safe update functions for the FSM displays,
# image display, and logging.
# -------------------------------------------------------------------
class DataTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Transfer Visualization & FSM")
        self.root.geometry("1100x800")

        # Simulation parameters and status variables.
        self.error_probability = 0.2  # 20% chance to simulate a packet error
        self.packets_sent = 0         # Count of successful transmissions (sender)
        self.packets_received = 0     # Count of successful transmissions (receiver)
        self.total_packets = len(get_file_data(file_path=FILE_PATH, packet_size=PACKET_SIZE))       # Total packets for simulation
        self.current_sender_state = 0 # Sender FSM state index
        self.current_receiver_state = 0  # Receiver FSM state index
        self.image_path = FILE_PATH  # Path to the image file to display
        self.running = False          # Flag for whether transfer is running

        # Build the GUI layout.
        self.create_frames()

    # -------------------------------------------------------------------
    # Construct the GUI frames (FSM displays, data canvas, controls, log).
    # -------------------------------------------------------------------
    def create_frames(self):
        # Top frame for FSM displays.
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill="both", expand=True)

        # Sender FSM frame.
        sender_frame = tk.LabelFrame(top_frame, text="Sender FSM", padx=10, pady=10)
        sender_frame.pack(side="left", padx=10, pady=10)
        self.sender_fsm_canvas = tk.Canvas(sender_frame, width=500, height=150, bg="white")
        self.sender_fsm_canvas.pack()

        # Receiver FSM frame.
        receiver_frame = tk.LabelFrame(top_frame, text="Receiver FSM", padx=10, pady=10)
        receiver_frame.pack(side="right", padx=10, pady=10)
        self.receiver_fsm_canvas = tk.Canvas(receiver_frame, width=300, height=150, bg="white")
        self.receiver_fsm_canvas.pack()

        # Middle frame for data-transfer visualization.
        middle_frame = tk.LabelFrame(self.root, text="Data Transfer Visualization", padx=10, pady=10)
        middle_frame.pack(pady=10, fill="both", expand=True)
        self.data_canvas = tk.Canvas(middle_frame, width=800, height=400, bg="gray")
        self.data_canvas.pack()

        # Bottom frame for controls and logging.
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10, fill="x")
        self.packet_info_label = tk.Label(bottom_frame, text="Packet Info: ", font=("Arial", 12))
        self.packet_info_label.pack(side="left", padx=10)
        start_btn = ttk.Button(bottom_frame, text="Start Transfer", command=self.start_transfer)
        start_btn.pack(side="left", padx=5)
        stop_btn = ttk.Button(bottom_frame, text="Stop Transfer", command=self.stop_transfer)
        stop_btn.pack(side="left", padx=5)
        reset_btn = ttk.Button(bottom_frame, text="Reset", command=self.reset_transfer)
        reset_btn.pack(side="left", padx=5)
        self.log_text = tk.Text(bottom_frame, height=4, width=70, font=("Arial", 10))
        self.log_text.pack(side="left", padx=10)
        self.log("Application started.")

    # -------------------------------------------------------------------
    # Log a message into the GUI log widget with a timestamp.
    # -------------------------------------------------------------------
    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S] ")
        self.log_text.insert("end", f"{timestamp}{message}\n")
        self.log_text.see("end")

    # -------------------------------------------------------------------
    # Draw the FSM on a canvas: draw rectangular boxes for each state.
    # The current active state is highlighted in light green.
    # -------------------------------------------------------------------
    def draw_fsm(self, canvas, states, current_index):
        canvas.delete("all")
        box_width = 120
        box_height = 50
        gap = 20
        x_offset = 20
        y_offset = 40
        for i, s in enumerate(states):
            x1 = x_offset + i * (box_width + gap)
            y1 = y_offset
            x2 = x1 + box_width
            y2 = y1 + box_height
            fill = "lightgreen" if i == current_index else "white"
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="black", width=2)
            canvas.create_text((x1+x2)/2, (y1+y2)/2, text=s, font=("Arial", 10), width=box_width-10)
            if i < len(states) - 1:
                arrow_x = x2 + gap/2
                arrow_y = (y1+y2)/2
                canvas.create_line(x2, arrow_y, arrow_x, arrow_y, arrow=tk.LAST, width=2)

    # -------------------------------------------------------------------
    # Update both the sender and receiver FSM displays.
    # -------------------------------------------------------------------
    def update_fsm_displays(self):
        self.draw_fsm(self.sender_fsm_canvas, sender_states, self.current_sender_state)
        self.draw_fsm(self.receiver_fsm_canvas, receiver_states, self.current_receiver_state)

    # -------------------------------------------------------------------
    # Update the data transfer image: crop and display the image representing progress.
    # -------------------------------------------------------------------
    def update_image(self, packets_sent, total_packets):
        try:
            img = Image.open(self.image_path)
            width, height = img.size
            progress_height = int((packets_sent / total_packets) * height)
            if progress_height <= 0:
                progress_height = 1
            cropped = img.crop((0, 0, width, progress_height))
            img_tk = ImageTk.PhotoImage(cropped)
            self.data_canvas.delete("all")
            self.data_canvas.create_image(400, 200, image=img_tk)
            self.data_canvas.image = img_tk  # Keep a reference
        except Exception as e:
            self.log(f"Error updating image: {e}")

    # -------------------------------------------------------------------
    # Thread–safe update methods: schedule updates in the main Tkinter thread.
    # -------------------------------------------------------------------
    
    # Defines a method to update the sender's state.
    def update_sender_state(self, new_state_index):  
        # Schedules the actual state update to run on the event loop.
        self.root.after(0, lambda: self._update_sender_state(new_state_index))

    # Internal method to perform the sender state update.
    def _update_sender_state(self, new_state_index):  
        # Sets the current sender state to the new state index.
        self.current_sender_state = new_state_index  
        # Updates the finite state machine displays to reflect the change.
        self.update_fsm_displays()  

    # Defines a method to update the receiver's state.
    def update_receiver_state(self, new_state_index):  
        # Schedules the actual state update to run on the event loop.
        self.root.after(0, lambda: self._update_receiver_state(new_state_index))

    # Internal method to perform the receiver state update.
    def _update_receiver_state(self, new_state_index):  
        # Sets the current receiver state to the new state index.
        self.current_receiver_state = new_state_index  
        # Updates the finite state machine displays to reflect the change.
        self.update_fsm_displays()  

    # Updates the text information displayed about the packet.
    def update_packet_info(self, info_text):  
        # Schedules a UI update to change the packet information label's text.
        self.root.after(0, lambda: self.packet_info_label.config(text=info_text))  

    # Logs an event by adding a message to the log display.
    def log_event(self, message):  
        # Schedules the log message addition to run on the event loop.
        self.root.after(0, lambda: self.log(message))  

    # -------------------------------------------------------------------
    # Control functions for starting, stopping, and resetting the transfer.
    # -------------------------------------------------------------------
    def start_transfer(self):
        self.running = True
        self.log("Transfer started.")
        # Start sender and receiver threads.
        threading.Thread(target=sender_thread, args=(self,), daemon=True).start()
        threading.Thread(target=receiver_thread, args=(self,), daemon=True).start()
    
    def stop_transfer(self):
        self.running = False
        self.log("Transfer paused.")
    
    def reset_transfer(self):
        self.running = False
        self.packets_sent = 0
        self.current_sender_state = 0
        self.current_receiver_state = 0
        self.data_canvas.delete("all")
        self.update_fsm_displays()
        self.packet_info_label.config(text="Packet Info: Reset")
        self.log("Transfer reset.")
    
    # -------------------------------------------------------------------
    # Control functions for receiver thread.
    # -------------------------------------------------------------------


# -------------------------------------------------------------------
# Sender thread simulates sending packets. In a real implementation,
# it would handle network communication. On each successful send,
# it updates the sender FSM and places packet info in a shared queue.
# -------------------------------------------------------------------
def sender_thread(app):
    # Define a separate thread function for the sender.
    # This function simulates sending packets and updating the FSM (Finite State Machine).
    # The `app` parameter is the GUI application instance, allowing the sender to interact with the GUI.

    # Create a UDP socket for sending data
    senderSocket = socket(AF_INET, SOCK_DGRAM)  # Using IPv4 and UDP protocol
    # Bind the socket to the local address and port
    senderSocket.bind(('', HOST_A_PORT))
    # Print a readiness message for the sender
    app.log_event("The HOST_A is Ready to Transmit a file")

    start = True

    while app.running and app.packets_sent < app.total_packets:
        # Continuously send packets while the transfer is running (`app.running`)
        # and the number of packets sent is less than the total packets required.
        ##################################################################################################################
        # Prompt the user for input: send data or terminate the program

        if start:
            user_choice = 'y' #get_user_choice()
            start = False
        else:
            user_choice = 'n'


        if user_choice == 'y':  # If the user chooses to send data

            # Initialize the state machine to STATE_0
            app.current_sender_state = 0 #Intial state

            seq_num = 0  # Initialize the sequence number (starting with 0)

            data = get_file_data()  # Fetch the file data and break it into packets
            
            if not data:  # If no data is retrieved (e.g., file not found or empty)
                pass    # Remain in the current state   
                #current_state = transition(state.STATE_0.name, 'STAY')  
            else:
                # Iterate through each packet of data
                for index, segment in enumerate(data):
                    while True:  # Keep trying to send the current packet until it is acknowledged
                        try: 
                            #sender_states
                            # Handle STATE_0: Initial state of the sender
                            if app.current_sender_state == 0:
                                app.log_event(f"Sender current state: " + sender_states[app.current_sender_state])  # Debugging: Print the current state
                                
                                # Send the current data packet with the sequence number
                                rdt_send(senderSocket, HOST_B_ADDRESS, segment, seq_num)

                                # Successful transmission: update sender state and send packet.
                                # If no error is simulated, proceed with the successful transmission logic.

                                packet_info = {"packet_num": app.packets_sent + 1, "timestamp": time.time()}
                                # Create a dictionary to hold information about the packet, such as its number
                                # and the timestamp when it was sent.

                                packet_queue.put(packet_info)
                                # Place the packet information in the shared queue to simulate transferring the packet
                                # to the receiver (GUI).

                                # Advance sender FSM state cyclically.
                                new_sender_state = (app.current_sender_state + 1) % len(sender_states)
                                # Calculate the next state in the sender FSM. The state index is incremented cyclically,
                                # wrapping around to the beginning using the modulo operator.

                                app.update_sender_state(new_sender_state)
                                # Update the sender FSM display in the GUI by notifying it of the new state.

                            # Handle STATE_1: Waiting for acknowledgment from the receiver
                            elif app.current_sender_state == 1:
                                app.log_event(f"Sender current state: " + sender_states[app.current_sender_state])  # Debugging: Print the current state
                                
                                # Receive the acknowledgment (ACK) from the receiver
                                rcvpacket, addr = senderSocket.recvfrom(6)  # Receive ACK packet (6 bytes)
                                # Extract the components of the ACK (checksum, sequence number, data)
                                received_checksum, received_seq_num, ACK = extract(rcvpacket)

                                # Simulate a percentage chance of ACK (Acknowledgment) corruption (OPTION 2)
                                '''
                                if random.random() < app.error_probability:  # Probability threshold for ACK corruption (currently set to always false since 0.0 is the condition)
                                    ACK = int.from_bytes(ACK, byteorder='big')  # Convert bytes to an integer
                                    ACK ^= 1 #Note: Tried to use this statment only and it was giving me an error
                                    ACK = ACK.to_bytes(1, byteorder='big')  # Convert the integer back to a bytes object
                                '''
                                    
                                # Calculate checksum to validate the integrity of the received ACK
                                computed_checksum = calculate_checksum(seq_num, ACK)

                                # Check if the ACK is corrupted
                                if computed_checksum == received_checksum:
                                    
                                    # Check if the sequence number in the ACK is incorrect
                                    if received_seq_num == seq_num:
                                        # Valid ACK received; debug and log its details
                                        # Transition to the next state
                                        # Advance sender FSM state cyclically.
                                        new_sender_state = (app.current_sender_state + 1) % len(sender_states)
                                        # Calculate the next state in the sender FSM. The state index is incremented cyclically,
                                        # wrapping around to the beginning using the modulo operator.

                                        app.update_sender_state(new_sender_state)
                                        # Update the sender FSM display in the GUI by notifying it of the new state.

                                        app.log_event(f"Sender: ACK {seq_num} received successfully.")
                                        # Log an event to indicate that the packet was sent successfully.
                                        
                                        app.packets_sent += 1
                                        # Increment the count of successfully sent packets.

                                        app.log_event(f"Sender: Packet {app.packets_sent} sent successfully.")
                                        # Log an event to indicate that the packet was sent successfully.

                                        app.update_packet_info(f"Packet {app.packets_sent}/{app.total_packets} transmitted")
                                        # Update the packet info in the GUI to show the successful transmission.

                                        # Toggle the sequence number for the next data packet
                                        seq_num = 1 - seq_num 


                                    else:
                                        #current_state = transition(state.STATE_1.name, 'STAY')  # Stay in the same state
                                        # Raise an exception if the ACK sequence is out of order
                                        #raise ValueError
                                        app.log_event("Sender: Error detected, ACK is out of sequence, retransmitting...")
                                        # Log an error message indicating that the packet is corrupted and will be retransmitted.

                                        app.update_packet_info(f"Packet {app.packets_sent+1}/{app.total_packets} - ERROR, retransmission")
                                        # Update the packet info on the GUI to display the error and retransmission.
                                        # Do not increment the packet count or update the sender state, simulating a `STAY` transition.
                                        rdt_send(senderSocket, HOST_B_ADDRESS, segment, seq_num)  # Resend the current packet
                                        
                                else:
                                    #current_state = transition(state.STATE_1.name, 'STAY')  # Stay in the same state
                                    # Raise an exception if the ACK is corrupted
                                    #raise ValueError
                                    app.log_event("Sender: Error detected, ACK is corrupted, retransmitting...")
                                    # Log an error message indicating that the packet is corrupted and will be retransmitted.

                                    app.update_packet_info(f"Packet {app.packets_sent+1}/{app.total_packets} - ERROR, retransmission")
                                    # Update the packet info on the GUI to display the error and retransmission.
                                    # Do not increment the packet count or update the sender state, simulating a `STAY` transition.
                                    rdt_send(senderSocket, HOST_B_ADDRESS, segment, seq_num)  # Resend the current packet


                            # Handle STATE_0: Initial state of the sender
                            elif app.current_sender_state == 2:
                                app.log_event(f"Sender current state: " + sender_states[app.current_sender_state])  # Debugging: Print the current state
                                
                                # Send the current data packet with the sequence number
                                rdt_send(senderSocket, HOST_B_ADDRESS, segment, seq_num)

                                # Successful transmission: update sender state and send packet.
                                # If no error is simulated, proceed with the successful transmission logic.

                                packet_info = {"packet_num": app.packets_sent + 1, "timestamp": time.time()}
                                # Create a dictionary to hold information about the packet, such as its number
                                # and the timestamp when it was sent.

                                packet_queue.put(packet_info)
                                # Place the packet information in the shared queue to simulate transferring the packet
                                # to the receiver (GUI).

                                # Advance sender FSM state cyclically.
                                new_sender_state = (app.current_sender_state + 1) % len(sender_states)
                                # Calculate the next state in the sender FSM. The state index is incremented cyclically,
                                # wrapping around to the beginning using the modulo operator.

                                app.update_sender_state(new_sender_state)
                                # Update the sender FSM display in the GUI by notifying it of the new state.

                            # Handle STATE_1: Waiting for acknowledgment from the receiver
                            elif app.current_sender_state == 3:
                                app.log_event(f"Sender current state: " + sender_states[app.current_sender_state])  # Debugging: Print the current state
                                
                                # Receive the acknowledgment (ACK) from the receiver
                                rcvpacket, addr = senderSocket.recvfrom(6)  # Receive ACK packet (6 bytes)
                                # Extract the components of the ACK (checksum, sequence number, data)
                                received_checksum, received_seq_num, ACK = extract(rcvpacket)

                                # Simulate a percentage chance of ACK (Acknowledgment) corruption (OPTION 2)
                                '''
                                if random.random() < app.error_probability:  # Probability threshold for ACK corruption (currently set to always false since 0.0 is the condition)
                                    ACK = int.from_bytes(ACK, byteorder='big')  # Convert bytes to an integer
                                    ACK ^= 1 #Note: Tried to use this statment only and it was giving me an error
                                    ACK = ACK.to_bytes(1, byteorder='big')  # Convert the integer back to a bytes object
                                '''
                                    
                                # Calculate checksum to validate the integrity of the received ACK
                                computed_checksum = calculate_checksum(seq_num, ACK)

                                # Check if the ACK is corrupted
                                if computed_checksum == received_checksum:
                                    
                                    # Check if the sequence number in the ACK is incorrect
                                    if received_seq_num == seq_num:
                                        # Valid ACK received; debug and log its details
                                        # Transition to the next state
                                        # Advance sender FSM state cyclically.
                                        new_sender_state = (app.current_sender_state + 1) % len(sender_states)
                                        # Calculate the next state in the sender FSM. The state index is incremented cyclically,
                                        # wrapping around to the beginning using the modulo operator.

                                        app.update_sender_state(new_sender_state)
                                        # Update the sender FSM display in the GUI by notifying it of the new state.

                                        app.log_event(f"Sender: ACK {seq_num} received successfully.")
                                        # Log an event to indicate that the packet was sent successfully.
                                        
                                        app.packets_sent += 1
                                        # Increment the count of successfully sent packets.

                                        app.log_event(f"Sender: Packet {app.packets_sent} sent successfully.")
                                        # Log an event to indicate that the packet was sent successfully.

                                        app.update_packet_info(f"Packet {app.packets_sent}/{app.total_packets} transmitted")
                                        # Update the packet info in the GUI to show the successful transmission.

                                        # Toggle the sequence number for the next data packet
                                        seq_num = 1 - seq_num 


                                    else:
                                        #current_state = transition(state.STATE_1.name, 'STAY')  # Stay in the same state
                                        # Raise an exception if the ACK sequence is out of order
                                        #raise ValueError
                                        app.log_event("Sender: Error detected, ACK is out of sequence, retransmitting...")
                                        # Log an error message indicating that the packet is corrupted and will be retransmitted.

                                        app.update_packet_info(f"Packet {app.packets_sent+1}/{app.total_packets} - ERROR, retransmission")
                                        # Update the packet info on the GUI to display the error and retransmission.
                                        # Do not increment the packet count or update the sender state, simulating a `STAY` transition.
                                        rdt_send(senderSocket, HOST_B_ADDRESS, segment, seq_num)  # Resend the current packet
                                        
                                else:
                                    #current_state = transition(state.STATE_1.name, 'STAY')  # Stay in the same state
                                    # Raise an exception if the ACK is corrupted
                                    #raise ValueError
                                    app.log_event("Sender: Error detected, ACK is corrupted, retransmitting...")
                                    # Log an error message indicating that the packet is corrupted and will be retransmitted.

                                    app.update_packet_info(f"Packet {app.packets_sent+1}/{app.total_packets} - ERROR, retransmission")
                                    # Update the packet info on the GUI to display the error and retransmission.
                                    # Do not increment the packet count or update the sender state, simulating a `STAY` transition.
                                    rdt_send(senderSocket, HOST_B_ADDRESS, segment, seq_num)  # Resend the current packet

                            else:
                                # Raise an exception if an invalid state is encountered
                                raise SystemExit("State machine entered an invalid state.")
                            
                            time.sleep(0.5)  # Simulate delay between packet sends
                            # Introduce a delay of 1 second between packet transmissions to simulate network latency.

                        #except ValueError as ve:
                            # Handle exceptions for corrupt or out-of-order packets
                            #print(ve)
                            

                        except SystemExit as re:
                            # Handle system termination
                            print(re)
                            print("Program terminated")
                
                app.log_event("Sender: All packets sent.")
                # Once all packets have been sent, log a final message to indicate that the sender has completed its job.
        
        elif user_choice == 'n':  # If the user chooses to terminate the program
            print("Program terminated")
            break  # Exit the program
# -------------------------------------------------------------------
# Receiver thread continuously monitors the packet_queue.
# Upon receiving a packet, it updates the receiver FSM and logs the event.
# -------------------------------------------------------------------
def receiver_thread(app):
    # Define the receiver thread function.
    # This function continuously monitors a shared packet queue for incoming packets,
    # processes them, and updates the receiver FSM in the GUI.
    # The `app` parameter is the GUI application instance, which allows updates to the GUI.
    
    # Create a UDP socket for communication
    receiverSocket = socket(AF_INET, SOCK_DGRAM)  # Using IPv4 and UDP

    # Bind the socket to the local address and specified port
    receiverSocket.bind(('', HOST_B_PORT))

    # Initialize the state machine to STATE_0 (Initial state)
    app.current_receiver_state = 0

    # Initialize the expected sequence number to 0
    expected_seq_num = 0

    # Byte array to store the data received
    received_data = bytearray()

    # Display readiness message to the sender
    app.log_event("The HOST_B is Ready to receive a new file")

    while app.running or not packet_queue.empty():
        # Keep running the receiver loop while the transfer is active (`app.running`)
        # OR there are still packets in the queue to process (`not packet_queue.empty()`).

        try:
            # Set the socket timeout (in seconds)
            receiverSocket.settimeout(2)  # 2 seconds timeout

            packet_info = packet_queue.get(timeout=2)  # Wait up to 2 seconds for a packet
            # Attempt to retrieve a packet from the shared packet queue.
            # If no packet is received within 2 seconds, raise a `queue.Empty` exception.

            packet, clientAddress = receiverSocket.recvfrom(HEADER_SIZE + PACKET_SIZE)

            if packet:
                
                app.log_event(f"Receiver current state: " + receiver_states[app.current_receiver_state])

                # Extract packet components and calculate checksum
                received_checksum, received_seq_num, data = extract(packet)

                computed_checksum = calculate_checksum(received_seq_num, data)

                # Check for packet corruption
                if computed_checksum == received_checksum:
                    # Check for out-of-order sequence numbers
                    if expected_seq_num == received_seq_num:

                        # Append received data to the data buffer
                        received_data.extend(data)

                        # Create an acknowledgment (ACK) packet
                        ACK = struct.pack("B", 1)  # ACK type 1
                        response = make_pkt(expected_seq_num, ACK)  # Send current sequence value
                        receiverSocket.sendto(response, clientAddress)  # Send ACK back to sender

                        # Display details of the valid packet for debugging
                        app.packets_received += 1
                        #app.log_event(f"Receiver: Packet_{app.packets_received} received: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                                                
                        # Toggle the sequence number for the next packet
                        expected_seq_num = 1 - expected_seq_num

                        # Transition to the next state
                        #current_state = transition(state.STATE_0.name, 'NEXT')

                        new_receiver_state = (app.current_receiver_state + 1) % len(receiver_states)
                        # Calculate the next state for the receiver FSM.
                        # Advance cyclically through the receiver_states list using modulo arithmetic.

                        app.update_receiver_state(new_receiver_state)
                        # Update the receiver FSM display in the GUI to reflect the new state.

                        app.log_event(f"Receiver: Packet {packet_info['packet_num']} received.")
                        # Log an event in the GUI to indicate that a packet has been successfully received.
                        # The packet number is extracted from the `packet_info` dictionary.

                        packet_queue.task_done()
                        # Indicate that the packet has been fully processed, allowing the queue to release it.

                        # Check if the packet size indicates the end of the file
                        if is_final_packet(packet):
                            break  # End of file, exit inner loop
                    
                    else:
                        
                        # Stay in the same state if sequence is out of order
                        #current_state = transition(state.STATE_0.name, 'STAY')
                        #raise ValueError
                        app.log_event("Receiver: sequence error detected, retransmitting previous sequence value...")
                        # Retransmit the previous sequence number
                        ACK = struct.pack("B", 1)
                        response = make_pkt(1 - expected_seq_num, ACK)  # Send previous sequence value
                        receiverSocket.sendto(response, clientAddress)
                else:
                    # Stay in the same state if data is corrupt
                    #current_state = transition(state.STATE_0.name, 'STAY')
                    #raise ValueError
                    app.log_event("Reiver: ACK error detected, ACK is Corrupt, retransmitting...")
                    #print(f"Packet Received, but data is Corrupt: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                    # Retransmit the previous sequence number
                    ACK = struct.pack("B", 1)
                    response = make_pkt(1 - expected_seq_num, ACK)  # Send previous sequence value
                    receiverSocket.sendto(response, clientAddress)
            else:
                break  # No packet received, end reception
         
        except queue.Empty or socket.timeout:
            # If no packets are received within the 2-second timeout, handle the exception.

            app.log_event("Receiver: Waiting for packets...")
            # Log a message indicating that the receiver is waiting for packets.

        time.sleep(0.5)  # Small delay before checking for the next packet
        # Introduce a short delay of 0.5 seconds before attempting to process the next packet.
        # This prevents the thread from continuously spinning in case the queue is empty.

    deliver_data(received_data, 1)
    receiverSocket.close()
    app.log_event("Receiver: Transfer complete.")
    # Once the loop ends (when the transfer stops and the queue is empty), log a message
    # to indicate that the receiver has completed processing all packets.

# -------------------------------------------------------------------
# Integration: Create the Tkinter root window, instantiate the GUI app,
# and start the Tkinter main event loop.
# -------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = DataTransferApp(root)
    root.mainloop()
