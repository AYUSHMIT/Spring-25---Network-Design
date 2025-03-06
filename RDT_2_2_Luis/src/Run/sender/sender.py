from sender_functions import *  # Importing required functions and modules from sender_functions


#----------------------------------------
'''Main program begins'''
#----------------------------------------
ACK_CORRUPTION_RATE = 0.1  # Simulated probability of acknowledgment corruption

# Main loop to keep the program running until the user chooses to exit
while True:
    # Prompt the user for input: send data or terminate the program
    user_choice = get_user_choice()

    if user_choice == 'y':  # If the user chooses to send data

        # Initialize the state machine to STATE_0
        current_state = state.STATE_0.name

        seq_num = 0  # Initialize the sequence number (starting with 0)

        data = get_file_data()  # Fetch the file data and break it into packets
        
        if not data:  # If no data is retrieved (e.g., file not found or empty)
            current_state = transition(state.STATE_0.name, 'STAY')  # Remain in the current state
        else:
            # Iterate through each packet of data
            for index, segment in enumerate(data):
                while True:  # Keep trying to send the current packet until it is acknowledged
                    try: 
                        # Handle STATE_0: Initial state of the sender
                        if current_state == state.STATE_0.name:
                            print(state.STATE_0.value)  # Debugging: Print the current state
                            
                            # Send the current data packet with the sequence number
                            rdt_send(segment, seq_num)
                            print(f"Sent Packet {index}")  # Debugging: Confirm packet sent
                            
                            # Transition to the next state (waiting for acknowledgment)
                            current_state = transition(state.STATE_0.name, 'NEXT')

                        # Handle STATE_1: Waiting for acknowledgment from the receiver
                        elif current_state == state.STATE_1.name:
                            print(state.STATE_1.value)  # Debugging: Print the current state
                            
                            # Receive the acknowledgment (ACK) from the receiver
                            rcvpacket, addr = senderSocket.recvfrom(6)  # Receive ACK packet (6 bytes)
                            # Extract the components of the ACK (checksum, sequence number, data)
                            received_checksum, received_seq_num, ACK = extract(rcvpacket)

                            # Simulate a percentage chance of ACK (Acknowledgment) corruption (OPTION 2)
                            if random.random() < ACK_CORRUPTION_RATE:  # Probability threshold for ACK corruption (currently set to always false since 0.0 is the condition)
                                ACK = int.from_bytes(ACK, byteorder='big')  # Convert bytes to an integer
                                ACK ^= 1 #Note: Tried to use this statment only and it was giving me an error
                                ACK = ACK.to_bytes(1, byteorder='big')  # Convert the integer back to a bytes object
                                
                            # Calculate checksum to validate the integrity of the received ACK
                            computed_checksum = calculate_checksum(seq_num, ACK)

                            # Check if the ACK is corrupted
                            if computed_checksum == received_checksum:
                                
                                # Check if the sequence number in the ACK is incorrect
                                if received_seq_num == seq_num and ACK == b'\x01':
                                    # Valid ACK received; debug and log its details
                                    print(f"Sender: ACK_{seq_num} received")
                                    print(f"ACK_{seq_num} Details: ACK={ACK}, rcv_seq_num={received_seq_num}, expected_seq={seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(rcvpacket)}")
                                    # Toggle the sequence number for the next data packet
                                    seq_num = 1 - seq_num  
                                    # Transition to the next state
                                    current_state = transition(state.STATE_1.name, 'NEXT')
                                    break  # Exit the loop to proceed to the next data segment
                                else:
                                    current_state = transition(state.STATE_1.name, 'STAY')  # Stay in the same state
                                    # Raise an exception if the ACK sequence is out of order
                                    #raise ValueError
                                    print(f"Sender: ACK_{seq_num} Received, but sequence is out of order: ACK={ACK}, rcv_seq_num={received_seq_num}, expected_seq={seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(rcvpacket)}")
                                    print(f"Re-transmitting Packet {index}")
                                    rdt_send(segment, seq_num)  # Resend the current packet
                                    
                            else:
                                current_state = transition(state.STATE_1.name, 'STAY')  # Stay in the same state
                                # Raise an exception if the ACK is corrupted
                                #raise ValueError
                                print(f"ACK_{seq_num} Received, but data is Corrupt: ACK={ACK}, rcv_seq_num={received_seq_num}, expected_seq={seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(rcvpacket)}")
                                print(f"Re-transmitting Packet {index}")
                                rdt_send(segment, seq_num)  # Resend the current packet


                        # Handle custom STATE_2 (if applicable)
                        elif current_state == state.STATE_2.name:
                            print(state.STATE_2.value)  # Debugging: Print the current state
                            
                            # Resend the current packet
                            rdt_send(segment, seq_num)
                            print(f"Sent Packet {index}")
                            
                            # Transition to the next state
                            current_state = transition(state.STATE_2.name, 'NEXT')

                        # Handle custom STATE_3 (if applicable)
                        elif current_state == state.STATE_3.name:
                            print(state.STATE_3.value)  # Debugging: Print the current state
                            
                            # Receive acknowledgment from the receiver
                            rcvpacket, addr = senderSocket.recvfrom(6)
                            received_checksum, received_seq_num, ACK = extract(rcvpacket)
                            
                            # Simulate a percentage chance of ACK (Acknowledgment) corruption (OPTION 2)
                            if random.random() < ACK_CORRUPTION_RATE:  # Probability threshold for ACK corruption (currently set to always false since 0.0 is the condition)
                                ACK = int.from_bytes(ACK, byteorder='big')  # Convert bytes to an integer
                                ACK ^= 1 #Note: flip the last bit, Tried to use this statment only without converting from byte to int, back and forth (above and below this line), and it was giving me an error
                                ACK = ACK.to_bytes(1, byteorder='big')  # Convert the integer back to a bytes object

                            computed_checksum = calculate_checksum(seq_num, ACK)

                            # Check if the received ACK is corrupted
                            if computed_checksum == received_checksum:

                                # Check if the ACK sequence number is incorrect
                                if received_seq_num == seq_num and ACK == b'\x01':
                                    # Valid ACK received; debug and log its details
                                    print(f"Sender: ACK_{seq_num} received")
                                    print(f"ACK_{seq_num} Details: ACK={ACK}, rcv_seq_num={received_seq_num}, expected_seq={seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(rcvpacket)}")
                                    
                                    # Toggle the sequence number for the next data packet
                                    seq_num = 1 - seq_num  
                                    # Transition to the next state
                                    current_state = transition(state.STATE_3.name, 'NEXT')
                                    break  # Exit the loop to proceed to the next data segment
                                else:
                                    current_state = transition(state.STATE_3.name, 'STAY')  # Stay in the same state
                                    #raise ValueError
                                    print(f"Sender: ACK_{seq_num} Received, but sequence is out of order: ACK={ACK}, rcv_seq_num={received_seq_num}, expected_seq={seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(rcvpacket)}")
                                    print(f"Re-transmitting Packet {index}")
                                    rdt_send(segment, seq_num)  # Resend the current packet
                                        
                            else:
                                current_state = transition(state.STATE_3.name, 'STAY')  # Stay in the same state
                                #raise ValueError
                                print(f"ACK_{seq_num} Received, but data is Corrupt: ACK={ACK}, rcv_seq_num={received_seq_num}, expected_seq={seq_num}, received_checksum={received_checksum}, calculated_checksum={computed_checksum}, data_length={len(rcvpacket)}")
                                print(f"Re-transmitting Packet {index}")
                                rdt_send(segment, seq_num)  # Resend the current packet
                        else:
                            # Raise an exception if an invalid state is encountered
                            raise SystemExit("State machine entered an invalid state.")

                    #except ValueError as ve:
                        # Handle exceptions for corrupt or out-of-order packets
                        #print(ve)
                        

                    except SystemExit as re:
                        # Handle system termination
                        print(re)
                        print("Program terminated")
                    
    elif user_choice == 'n':  # If the user chooses to terminate the program
        print("Program terminated")
        break  # Exit the program
    else:  # If invalid input is provided, remain in the current state
        current_state = transition

#----------------------------------------
'''End Main program'''
#----------------------------------------