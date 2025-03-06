# Notes:
# Run Receiver first: Make sure the Receiver is running before you start the sender

# Importing necessary Python libraries and custom functions
from receiver_functions import *  # Import custom functions for receiver operations
import math  # Import math library for mathematical operations

# ----------------------------------------
'''Main program begins'''
# ----------------------------------------
counter = 1  # Counter to enumerate the output files with numbers

# Run the receiver in an infinite loop to continuously handle incoming files
while True:
    
    # Initialize the state machine to STATE_0 (Initial state)
    current_state = state.STATE_0.name
    # Initialize the expected sequence number to 0
    expected_seq_num = 0
    # Byte array to store the data received
    received_data = bytearray()

    # Display readiness message to the sender
    print("The HOST_B is Ready to receive a new file")

    # Handle receiving of packets in an inner loop
    while True:
        try:
            # Receive a packet from the sender along with the client's address
            packet, clientAddress = receiverSocket.recvfrom(PACKET_SIZE + 5)  # Packet size plus header bytes

            if packet:
                # If the current state is STATE_0
                if current_state == state.STATE_0.name:  # Initial state, waiting for sequence number 1
                    print(state.STATE_0.value)  # Print the current state for debugging

                    # Extract packet components and calculate checksum
                    received_checksum, received_seq_num, data = extract(packet)
                    

                    computed_checksum = calculate_checksum(received_seq_num, data)

                    # Check for packet corruption
                    if computed_checksum == received_checksum:
                        # Check for out-of-order sequence numbers
                        if expected_seq_num == received_seq_num:
                            
                            # Valid packet received
                            print(f"Sender: Valid packet received")

                            # Append received data to the data buffer
                            received_data.extend(data)

                            # Create an acknowledgment (ACK) packet
                            ACK = struct.pack("B", 1)  # ACK type 1
                            response = make_pkt(expected_seq_num, ACK)  # Send current sequence value
                            receiverSocket.sendto(response, clientAddress)  # Send ACK back to sender

                            # Display details of the valid packet for debugging
                            print(f"Packet_{expected_seq_num} Details: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                            
                            # Check if the packet size indicates the end of the file
                            if is_final_packet(packet):
                                break  # End of file, exit inner loop
                            
                            # Toggle the sequence number for the next packet
                            expected_seq_num = 1 - expected_seq_num

                            # Transition to the next state
                            current_state = transition(state.STATE_0.name, 'NEXT')
                        
                        else:
                            
                            # Stay in the same state if sequence is out of order
                            current_state = transition(state.STATE_0.name, 'STAY')
                            #raise ValueError
                            print(f"Packet Received, but sequence is out of order: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                            # Retransmit the previous sequence number
                            ACK = struct.pack("B", 1)
                            response = make_pkt(1 - expected_seq_num, ACK)  # Send previous sequence value
                            receiverSocket.sendto(response, clientAddress)
                    else:
                        # Stay in the same state if data is corrupt
                        current_state = transition(state.STATE_0.name, 'STAY')
                        #raise ValueError
                        print(f"Packet Received, but data is Corrupt: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                        # Retransmit the previous sequence number
                        ACK = struct.pack("B", 1)
                        response = make_pkt(1 - expected_seq_num, ACK)  # Send previous sequence value
                        receiverSocket.sendto(response, clientAddress)

                # If the current state is STATE_1
                elif current_state == state.STATE_1.name:  # Waiting for sequence number 1
                    print(state.STATE_1.value)  # Print the current state for debugging

                    # Extract packet components and calculate checksum
                    received_checksum, received_seq_num, data = extract(packet)
                    computed_checksum = calculate_checksum(received_seq_num, data)

                    # Check for packet corruption
                    if computed_checksum == received_checksum:

                        # Check for out-of-order sequence numbers
                        if expected_seq_num == received_seq_num:
                            # Valid packet received
                            print(f"Sender: Valid packet received")

                            # Append received data to the data buffer
                            received_data.extend(data)

                            # Create an acknowledgment (ACK) packet
                            ACK = struct.pack("B", 1)  # ACK type 1
                            response = make_pkt(expected_seq_num, ACK)  # Send current sequence value
                            receiverSocket.sendto(response, clientAddress)  # Send ACK back to sender

                            # Display details of the valid packet for debugging
                            print(f"Packet_{expected_seq_num} Details: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                            
                            # Check if the packet size indicates the end of the file
                            if is_final_packet(packet):
                                break  # End of file, exit inner loop

                            # Toggle the sequence number for the next packet
                            expected_seq_num = 1 - expected_seq_num

                            # Transition to the next state
                            current_state = transition(state.STATE_1.name, 'NEXT')
                        else:
                            # Stay in the same state if sequence is out of order
                            current_state = transition(state.STATE_1.name, 'STAY')
                            #raise ValueError
                            print(f"Packet Received, but sequence is out of order: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                            
                            # Retransmit the previous sequence number
                            ACK = struct.pack("B", 1)
                            response = make_pkt(1 - expected_seq_num, ACK)  # Send previous sequence value
                            receiverSocket.sendto(response, clientAddress)
                    else:
                        
                        # Stay in the same state if data is corrupt
                        current_state = transition(state.STATE_1.name, 'STAY')
                        #raise ValueError
                        print(f"Packet Received, but data is Corrupt: rcv_seq_num={received_seq_num}, expected_seq={expected_seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(packet)}")
                       
                        # Retransmit the previous sequence number
                        ACK = struct.pack("B", 1)
                        response = make_pkt(1 - expected_seq_num, ACK)  # Send previous sequence value
                        receiverSocket.sendto(response, clientAddress)

                else:
                    # Raise an exception if an invalid state is encountered
                    raise SystemExit("State machine entered an invalid state. Program terminated")
                

            else:
                break  # No packet received, end reception

        
        # Handle exceptions for packet errors and retransmissions
        #except ValueError as ve:
            #print(ve)

        # Handle system exit exceptions
        except SystemExit as re:
            print(re)
            print("Program terminated")

    # Deliver the received data and save it
    if len(received_data) > PACKET_SIZE:
        deliver_data(received_data, counter)
        print(f"Total data received: {len(received_data)} bytes, # of Packages received: {math.ceil(len(received_data) / 1024)}")  # Print total received data details
        counter += 1  # Increment counter for the next file
    
    
# ----------------------------------------
'''End Main program'''
# ----------------------------------------