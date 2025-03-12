import socket
import struct
import random
import time

def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
        checksum &= 0xFFFFFFFF  # Keep it 32-bit
    return ~checksum & 0xFFFFFFFF

def make_rdt_packet(seq_num, data):
    checksum = calculate_checksum(data)
    header = struct.pack('!I B', checksum, seq_num)
    return header + data

def parse_rdt_packet(packet):
    header = packet[:5]
    data = packet[5:]
    checksum, seq_num= struct.unpack('!I B', header)
    return checksum, seq_num, data

def is_corrupt(packet):
    checksum, seq_num, data = parse_rdt_packet(packet)
    calculated_checksum = calculate_checksum(data)
    print(f"Original checksum: {checksum}, Calculated checksum: {calculated_checksum}")
    return calculated_checksum != checksum

def is_ack_corrupt(packet):
    checksum, seq_num, data = parse_rdt_packet(packet)
    return calculate_checksum(struct.pack('!I', seq_num)) != checksum

def make_ack_packet(seq_num):
    checksum = calculate_checksum(struct.pack('!I', seq_num))
    return struct.pack('!I B', checksum, seq_num)

def parse_ack_packet(packet):
    return struct.unpack('!I B', packet)

def make_packet(file_path, packet_size=1024):
    packets = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(packet_size)
            if not chunk:
                break
            packets.append(chunk)
    return packets

def create_udp_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)  # Set a shorter timeout for socket operations
    return sock

def send_packet(sock, packet, address):
    sock.sendto(packet, address)

def receive_packet(sock, buffer_size=1030):  # Increased buffer size to 1030 (1024 + 6 for header)
    return sock.recvfrom(buffer_size)

def send_file(file_path, update_fsm_state, option, error_rate, retry_count=3, address=('localhost', 12345)):
    packets = make_packet(file_path)
    sock = create_udp_socket()
    seq_num = 0

    for index, packet in enumerate(packets):
        rdt_packet = make_rdt_packet(seq_num, packet)
        try:
            
            send_packet(sock, rdt_packet, address)
            print(f"Client: Sent packet {index}")
            while True:
                #Wait for acknoledgement
                ack_packet, _ = receive_packet(sock) #checksum, seq_num
                ack_checksum, ack_seq_num = parse_ack_packet(ack_packet)
                # debug print comment or delete
                #print(f"Client: ack_seq_num = {ack_seq_num}, seq_num = {seq_num}, ack_checksum = {ack_checksum}, calculate_checksum = {calculate_checksum(ack_packet)}, iscorrupt = {is_corrupt(ack_packet)}")

                if random.random() < error_rate:
                    print(f"option2: Simulating ACK packet bit-error")
                    ack_seq_num = 1 - ack_seq_num  #flip sequence number to from 1 to 0
                    #continue  # Simulate packet loss

                if ack_seq_num == seq_num and not is_ack_corrupt(ack_packet):
                    print(f"Client: Received ACK for packet {index}")
                    seq_num = 1 - seq_num
                    break  #continue with next packet
                else: #acknoledgement corrupt or out of sequence, Retransmitting.
                    send_packet(sock, rdt_packet, address)  #resend current package
                    print(f"Client: ack is out of sequence, retransmitting packet {index}")
        except ConnectionResetError as e:
            print(f"ConnectionResetError: {e}")
            if retry_count > 0:
                print(f"Retrying... {retry_count} attempts left.")
                time.sleep(1)  # Reduced sleep duration
                send_file(file_path, update_fsm_state, option, error_rate, retry_count - 1, address)
                return
            else:
                update_fsm_state(f"Error sending packet {index}: {e}")
                return
        except socket.timeout:
            print(f"Timeout waiting for ACK for packet {index}")
            update_fsm_state(f"Timeout waiting for ACK for packet {index}")
            return
        except Exception as e:
            print(f"Error sending packet {index}: {e}")
            update_fsm_state(f"Error sending packet {index}: {e}")
            return
        update_fsm_state(f"Sent packet {index}")

    # Send an empty packet to indicate the end of the file transfer
    end_packet = make_rdt_packet(seq_num, b'')
    send_packet(sock, end_packet, address)
    print("Sent end of file packet")
    update_fsm_state("Sent end of file packet")

def corrupt_packet(packet):
    checksum, seq_num, data = parse_rdt_packet(packet)
    num_bytes_to_corrupt = random.randint(1, len(data))  # Randomly decide how many bytes to corrupt
    corrupted_data = bytearray(data)
    
    for _ in range(num_bytes_to_corrupt):
        index_to_corrupt = random.randint(0, len(data) - 1)
        corrupted_data[index_to_corrupt] ^= 0xFF  # Toggle bits to corrupt the byte
    
    
    header = struct.pack('!I B', checksum, seq_num)
    return header + bytes(corrupted_data)


def receive_file(update_fsm_state, option, error_rate, sock, listen_address, save_path):
    while True:
        try:
            sock.bind(listen_address)
            break
        except OSError as e:
            if e.errno == 10048:  # Address already in use
                listen_address = ('localhost', random.randint(10000, 20000))
            else:
                raise e

    received_packets = {}
    expected_seq_num = 0
    index = 0

    while True:
        try:
            rdt_packet, sender_address = receive_packet(sock)
            if random.random() < error_rate and parse_rdt_packet(rdt_packet)[2] != b'':
                print(f"Option 3: Simulating Data packet {index} bit-error")
                #old_rdt_packet = rdt_packet
                rdt_packet = corrupt_packet(rdt_packet)
                #print(f"old: {calculate_checksum(old_rdt_packet)}, new: {calculate_checksum(rdt_packet)}, is_corrupt(rdt_packet){is_corrupt(rdt_packet)}")

            if not is_corrupt(rdt_packet):
                _, seq_num, data = parse_rdt_packet(rdt_packet)
                if seq_num == expected_seq_num:
                    if data == b'':  # End of file packet
                        print("Server: Received end of file packet")
                        update_fsm_state("Received end of file packet")
                        break
                    received_packets[index] = data
                    ack_packet = make_ack_packet(expected_seq_num)
                    send_packet(sock, ack_packet, sender_address)
                    print(f"Server: Received packet {index}")
                    update_fsm_state(f"Received packet {index}")
                    expected_seq_num = 1 - expected_seq_num
                    index += 1
                    continue
                    
                else:
                    print(f"Server: packet {index} is out of sequence, retransmiting...")
                    ack_packet = make_ack_packet(1 - expected_seq_num)
                    send_packet(sock, ack_packet, sender_address)
            else:
                print(f"Server: packet {index} is data is corrupted, retransmiting...")
                ack_packet = make_ack_packet(1 - expected_seq_num)
                send_packet(sock, ack_packet, sender_address)
        except socket.timeout:
            print(f"Timeout waiting for packet {index}")
            update_fsm_state(f"Timeout waiting for packet{index}")
            return
        except Exception as e:
            print(f"Error receiving packet {index}: {e}")
            update_fsm_state(f"Error receiving packet {index}: {e}")
            return

    with open(save_path, 'wb') as f:
        for i in range(len(received_packets)):
            f.write(received_packets[i])
    print("File received successfully")
    update_fsm_state("File received successfully")
    sock.close()