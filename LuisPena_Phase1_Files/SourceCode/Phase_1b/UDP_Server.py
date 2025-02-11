#Notes: 
    #Run Server First: Make sure the server is running before you start the client

#including python libraries
from socket import *
import math
#End Python libraries

#function definitions
def receive_file(serverPort=12000, buffer_size=1024, output_file="received_file"):
    # Create a UDP socket
    serverSocket = socket(AF_INET, SOCK_DGRAM)  #Creates UDP socket
    
    # Bind the socket to the local address and port
    serverSocket.bind(('', serverPort))
    print("The server is ready to receive")
    
    counter = 1
    while True:  # Outer loop to continuously wait for new files
        received_data = bytearray()
        while True:  # Inner loop to receive packets
            packet, clientAddress = serverSocket.recvfrom(buffer_size)
            print(f"Received packet from {clientAddress}")  # Debug statement

            if packet:
                received_data.extend(packet)  # Add received packet to data
                
                if len(packet) < buffer_size:
                    # If the packet size is smaller than buffer_size, it indicates the end of the file
                    break
            else:
                break  # End reception if no packet is received

        print(f"Total data received: {len(received_data)} bytes, # of Packages received: {math.ceil(len(received_data)/1024)})")         # print total 
        
        # Write the received data to the output file
        with open(output_file + str(counter) + ".bmp", "wb") as f:  #Each file sent by client will generate a new .bmp image with name output_file#.bpm
            f.write(received_data)

        '''
        Note: with open(...) as f: construct, the file is automatically closed
              when the code block inside the with statement is exited
        '''

        print("File received successfully and written to disk")
        counter += 1
#End function definitions

#Server program begins.

receive_file()      # Run the server
