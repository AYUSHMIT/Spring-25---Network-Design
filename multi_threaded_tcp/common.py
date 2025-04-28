import threading

# Fake Packet class
class Packet:
    def __init__(self, seq_num, data):
        self.seq_num = seq_num
        self.data = data
        self.acknowledged = False
        self.sent_time = None

# Global Variables
send_buffer = []  # List of Packet objects waiting to be acknowledged
ack_buffer = []   # List of acknowledged sequence numbers

# Mutexes for thread-safe access
send_buffer_lock = threading.Lock()
ack_buffer_lock = threading.Lock()
timer_table_lock = threading.Lock()

# Timer Table: {seq_num: send_time}
timer_table = {}

# Congestion Control Variables
cwnd = 1  # Initial congestion window size
ssthresh = 16  # Slow start threshold
cwnd_lock = threading.Lock()

# Simulation Parameters
TIMEOUT = 2  # Timeout duration in seconds
PACKET_GEN_INTERVAL = 0.1  # Interval between packet generation in seconds