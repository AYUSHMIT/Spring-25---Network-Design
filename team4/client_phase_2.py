import time
from file_transfer import send_file

def update_fsm_state(state):
    print(f"FSM State: {state}")

if __name__ == "__main__":
    file_path = r'C:\Users\Luis D. Pena Mateo\OneDrive\Desktop\Spring2025\Spring-25---Network-Design\team4\phase_2_JPG_500kB.jpg'  # Replace with the actual path to your image file
    send_file(file_path, update_fsm_state, option=1, error_rate=0.0, ack_loss_rate = 0.0)
    while True:
        time.sleep(1)  # Keep the client running until the transfer is complete