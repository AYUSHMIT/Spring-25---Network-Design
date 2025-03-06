from sender_functions import *  # Importing required functions and modules from sender_functions
import time
import matplotlib.pyplot as plt

#----------------------------------------
'''Main program begins'''
#----------------------------------------
# Create a list of corruption rates ranging from 0 to 0.6 in increments of 0.05
corruption_rate_list = [i / 100 for i in range(0, 61, 5)]
# Uncomment to print corruption rates for debugging purposes
#print(corruption_rate_list)

# Main loop to keep the program running until the user chooses to exit
while True:
    # Prompt the user for input: send data or terminate the program
    user_choice = get_user_choice()

    if user_choice == 'y':  # If the user chooses to send data

        # Initialize a list to store average execution times for each corruption rate
        average_execution_time_list = []

        # Iterate through each corruption rate in the list
        for corruption_rate in corruption_rate_list:
            
            # Create a new list to store execution times for the current corruption rate
            time_list = []

            # Loop to run the test 10 times for the current corruption rate
            for i in range(10):

                # Record the start time before running the rdt_send function
                start_time = time.time()

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
                                    if random.random() < corruption_rate:  # Probability threshold for ACK corruption (currently set to always false since 0.0 is the condition)
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
                                    if random.random() < corruption_rate:  # Probability threshold for ACK corruption (currently set to always false since 0.0 is the condition)
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
            
                # Record the end time after the rdt_send function has executed
                end_time = time.time()

                # Calculate the execution time for the current iteration
                execution_time = end_time - start_time  

                # Append the calculated execution time to the time_list
                time_list.append(execution_time)

                # Print the execution time for the current iteration
                # The iteration count is human-readable (i+1)
                print(f"Execution time {i+1}: {time_list[i]} seconds")
                # Print a summary of all average execution times across all corruption rates

            # Calculate the average execution time for the current corruption rate
            # The average is the sum of all execution times divided by the number of iterations
            average = sum(time_list) / len(time_list)

            # Append the average execution time to the average_execution_time_list
            average_execution_time_list.append(average)

            # Print the average execution time for the current corruption rate
            print(f"Average Execution time: {average} seconds for corruption_rate: {corruption_rate}")

        # Print a summary of all average execution times across all corruption rates
        print(f"Summary of average: {average_execution_time_list}")
        # Create the plot
        plt.figure(figsize=(8, 6))  # Set figure size
        plt.plot(corruption_rate_list, average_execution_time_list, marker='o', linestyle='-', color='b', label='Avg Execution Time')

        # Add labels and title
        plt.title("Average Execution Time vs. Corruption Rate", fontsize=16)
        plt.xlabel("Corruption Rate", fontsize=14)
        plt.ylabel("Average Execution Time (seconds)", fontsize=14)

        # Add a grid for readability
        plt.grid(True)

        # Add a legend
        plt.legend(fontsize=12)

        #save plot
        plt.savefig("execution_time_vs_corruption_rate.png")

        # Display the plot
        plt.show()
 
    elif user_choice == 'n':  # If the user chooses to terminate the program
        print("Program terminated")
        break  # Exit the program
    else:  # If invalid input is provided, remain in the current state
        current_state = transition

#----------------------------------------
'''End Main program'''
#----------------------------------------