# logger.py

import os
import time

# Setup log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Files for different logs
CWND_LOG = os.path.join(LOG_DIR, "cwnd_log.txt")
RTT_LOG = os.path.join(LOG_DIR, "rtt_log.txt")
RTO_LOG = os.path.join(LOG_DIR, "rto_log.txt")
SIM_LOG = os.path.join(LOG_DIR, "simulation_log.txt")

def reset_logs():
    """Clear all logs at the start."""
    open(CWND_LOG, "w").close()
    open(RTT_LOG, "w").close()
    open(RTO_LOG, "w").close()
    open(SIM_LOG, "w").close()

def log(msg):
    """General simulation log (messages)."""
    timestamp = time.strftime('%H:%M:%S')
    formatted_msg = f"[{timestamp}] {msg}"
    print(formatted_msg)
    with open(SIM_LOG, "a") as f:
        f.write(formatted_msg + "\n")

def log_cwnd(timestamp, cwnd):
    with open(CWND_LOG, "a") as f:
        f.write(f"{timestamp:.4f} {cwnd}\n")

def log_rtt(timestamp, sample_rtt):
    with open(RTT_LOG, "a") as f:
        f.write(f"{timestamp:.4f} {sample_rtt:.6f}\n")

def log_rto(timestamp, timeout_interval):
    with open(RTO_LOG, "a") as f:
        f.write(f"{timestamp:.4f} {timeout_interval:.6f}\n")

