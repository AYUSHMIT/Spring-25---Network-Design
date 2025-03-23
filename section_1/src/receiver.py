import socket
import struct
import os
from .utils import calculate_checksum, verify_checksum, introduce_bit_error, simulate_loss, make_packet, extract_sequence_number, extract_data

PACKET_SIZE = 1024
ACK_SIGNAL = b'ACK'
DATA_LOSS_RATE = 0.2
ACK_LOSS_RATE = 0.2
BIT_ERROR_RATE = 0.1

def run_go_back_n_receiver(host, port, output_file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    expectedsegnum = 0
    received_data = b''

    try:
        with open(output_file, 'wb') as file:
            while True:
                packet, address = sock.recvfrom(PACKET_SIZE + 12)  # Adjust buffer size as needed
                if not packet:
                    break

                if not simulate_loss(DATA_LOSS_RATE):
                    packet = introduce_bit_error(packet, BIT_ERROR_RATE)

                if not verify_checksum(packet):
                    print("Checksum error, discarding packet")
                    ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
                    sock.sendto(ack_packet, address)
                    continue

                seq_num = extract_sequence_number(packet)

                if seq_num == expectedsegnum:
                    print(f"Received expected packet {seq_num}")
                    data = extract_data(packet)
                    received_data += data
                    file.write(data)
                    ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
                    if not simulate_loss(ACK_LOSS_RATE):
                        sock.sendto(ack_packet, address)
                    expectedsegnum += 1
                else:
                    print(f"Out-of-order packet {seq_num}, expected {expectedsegnum}")
                    ack_packet = make_packet(expectedsegnum, b'', packet_type=ACK_SIGNAL)
                    sock.sendto(ack_packet, address)

    except Exception as e:
        print(f"Receiver: An error occurred: {e}")
    finally:
        sock.close()
    return len(received_data)

if __name__ == "__main__":
    receiver_host = 'localhost'
    receiver_port = 5000
    output_file = 'received_image.bmp'

    run_go_back_n_receiver(receiver_host, receiver_port, output_file)