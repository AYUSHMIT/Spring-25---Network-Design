# logger.py
import time
import os

# Setup the log file path
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "simulation_log.txt")

# Create the logs folder if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    """Logs a message with timestamp to console AND to simulation_log.txt"""
    timestamp = time.strftime('%H:%M:%S')
    formatted_msg = f"[{timestamp}] {msg}"

    # Print to terminal
    print(formatted_msg)

    # Also write to file
    with open(LOG_FILE, "a") as f:
        f.write(formatted_msg + "\n")

def reset_log():
    """Reset simulation_log.txt by clearing old content at simulation start"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(f"=== New Simulation Log Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
