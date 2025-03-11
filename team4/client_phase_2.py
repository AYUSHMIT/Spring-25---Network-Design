import time
from file_transfer import send_file

def update_fsm_state(state):
    print(f"FSM State: {state}")

if __name__ == "__main__":
    file_path = 'C:/Users/Ayush_Pandey/Dev/Pandey_phase2/RDT/pandey/phase_2.jpg'  # Replace with the actual path to your image file
    send_file(file_path, update_fsm_state, option=1, error_rate=0.0)
    while True:
        time.sleep(1)  # Keep the client running until the transfer is complete