
from logging.config import valid_ident
import socket
import random
import time
# ************ function definitions ************

def Make_packet(file_to_read):
    #all of the packets that we are going to send out
    packets_to_send = []
    #open our file that is in the same directory of our python script
    with open(file_to_read, "rb") as file:
        #indefinitely loop our file
        while True:
            packet = file.read(1024)
            #once we have reached the end of our .bmp file, we need to exit our while loop
            if not packet:
                break
            packets_to_send.append(packet)

    return packets_to_send

def Create_checksum(packet, sequence_number):
                            
    return (sum(packet) + sequence_number) % 65536

def Udt_send_packet(packet):
    server_name = socket.gethostname()
    clientPort = 12000
    client_socket.sendto(packet, (server_name, clientPort))

def Rdt_recv_packet():
    message_from_server, server_address = client_socket.recvfrom(2048)
    return message_from_server

def ACK_corruption(percent_error, server_message):
    #create our error range
    percent_error = int(percent_error)

    ack_error = random.randint(0, 99)

    if(ack_error > percent_error):
        ack_error = 0
    else:
        ack_error = 1

    #corrupt the ack message
    if ack_error == 1:
       server_message = b"x" + server_message
    else:
        server_message = server_message

    return server_message



#setup the client UDP
#we will use a generic establishment, thus will work on any pc
server_name = socket.gethostname()
print("Host client name: " + server_name)
server_host_ip = socket.gethostbyname(server_name)
print("Host server IP: " + server_host_ip)
HOST = server_host_ip
client_port = 12000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"Client is now connected to the server")


#server connection has now been established. Now that we have our server working
#we should now work on splitting up our image

#source of image: https://people.math.sc.edu/Burkardt/data/bmp/bmp.html

#fileDir = os.environ.get("PythonApplication1")
file_name = "FattestCatEver.jpg"
#call our make packet function
output_image = Make_packet(file_name)
count = 0
seq_num = 0
valid_input = False

#Use a switch to decide course of action based on user input
while valid_input != True:

    #Create decision for the three options a user has for the packet development
    option_choice = input("Please choose an option in your option selection please match the casing of option names.\n Option 1: No loss/bit-errors \n Option 2: ACK packet bit-error \n Option 3: Data packet bit-error\n >")
    
    if (option_choice == "Option 1"):
        print("\n**** You have chosen option 1 ****")
        valid_input = True
        #tell server our option selection
        server_message = b"op1"
        client_socket.sendto(server_message, (server_name, client_port))
    elif (option_choice == "Option 2"):
        print("\n**** You have chosen option 2 ****")
        valid_input = True
        #tell server our option selection
        server_message = b"op2"
        client_socket.sendto(server_message, (server_name, client_port))
    elif (option_choice == "Option 3"):
        print("\n**** You have chosen option 3 ****")
        valid_input = True
        #tell server our option selection
        server_message = b"op3"
        client_socket.sendto(server_message, (server_name, client_port))
    else:
        print("You have either entered an invalid option or did not match the option casing, try again\n")
        valid_input = False

#all of our packets are now in our outputImage array, we now need to parse this array and send each packet one by one.

#**** Option 1 - No Loss ****
if(option_choice == "Option 1"):
    print("We will now transmit packets with absolutely no loss at any point\n")

    count = 0
    seq_num = 0
    start_time = time.time()
    for packet in output_image:
        # Adds sequence number to packet and checksum, creating the header
        count += 1
        print("Packet: ", count)
        check_sum = Create_checksum(packet, seq_num)
        print(f"Checksum: {check_sum}\n")
        check_sum = check_sum.to_bytes(2, "big")
        packet = check_sum + packet
        packet = seq_num.to_bytes(1, "big") + packet

        #send the packet to the server
        Udt_send_packet(packet)

        #recieve message from server
        message_from_server, server_address = client_socket.recvfrom(2048)

        #we now must wait for our server to tell us that it has processed our packet and then we can move on to our next packet
        while message_from_server != b"ack":
            if message_from_server == "resend":
                Udt_send_packet(packet)
            message_from_server = ""
            message_from_server, server_address = client_socket.recvfrom(2048)
        
        seq_num = (seq_num +1) % 2 # Using mod to make sure sequence number stays 0/1
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Completion Time: {elapsed_time: .10f} seconds.")


#**** Option 2 - ACK Corruption ****
#we need to send our clean packet out. Once this packet is sent we need to take in our 
#ACK/NAK message from the server and go through the aritificial corruption chances
#In the case of corruption, we know that we are only expecting ACK/NAK on the client side
#If this message is not present, we will wait for the server resend it's ACK/NAK message until we move forward
elif(option_choice == "Option 2"):
    print("Implementation of ACK corruption\n")
    count = 0
    seq_num = -1
    start_time = time.time()
    while True:
        percent_error = input("Please select the percentage of ACK corruption you would like to be implemented(0-60 increments of 5 is the range): ")
        if percent_error == 0 or 5 or 10 or 15 or 20 or 25 or 30 or 35 or 40 or 45 or 50 or 55 or 60:
            break
        else:
            percent_error = input("invalid value, try again")

    for packet in output_image:
        count += 1
        #create the header for the packet
        seq_num = (seq_num +1) % 2
        check_sum = Create_checksum(packet, seq_num)
        print(f"\nPacket {count} Checksum: {check_sum}")
        check_sum = check_sum.to_bytes(2, "big")
        header = seq_num.to_bytes(1, "big") + check_sum

        #attach header to packet
        packet_to_send = header + packet

        #send the packet to the server
        Udt_send_packet(packet_to_send)
        #seq_num = (seq_num +1) % 2

        #listen for message back from server
        message_from_server = ""
        message_from_server, server_address = client_socket.recvfrom(2048)

        message_from_server = ACK_corruption(percent_error, message_from_server)

        while message_from_server != b"ack":
            #treat NAK and corruption the same
            print("The previous packet either had corruption, or the ACK/NAK message could not be processed")
            print(f"\nThe packet {count} will be resent")
            #create the header for the packet
            check_sum = Create_checksum(packet, seq_num)
            print(f"Resent Packet Checksum: {check_sum}")
            check_sum = check_sum.to_bytes(2, "big")
            header = seq_num.to_bytes(1, "big") + check_sum

            #attach header to packet
            packet_to_send = header + packet

            #resend the packet to the server
            Udt_send_packet(packet_to_send)
            count += 1

            #wait for server response
            message_from_server = ""
            message_from_server, serverAddress = client_socket.recvfrom(2048)

            #do our randomized courruption again
            message_from_server = ACK_corruption(percent_error, message_from_server)
            if(message_from_server == b"ack"):
                count - 1
                print(f"Packet {count} sent without corruption in DATA and no corruption in ACK\n")
                break
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Completion Time: {elapsed_time: .10f} seconds.")

        #we recieved an ACK we can move forward to our next pack to be processed
        #seq_num = (seq_num +1) % 2 # Using mod to make sure sequence number stays 0/
            
#**** Option 3 - ACK Corruption ****
#we are just going to send the packet to the server.
#server will be responsible for corrupting the data portion of the packet
elif(option_choice == "Option 3"):
    print("Server-side data corruption\n")
    count = 0
    seq_num = -1
    start_time = time.time()
    for packet in output_image:
        count += 1
        #create the header for the packet
        seq_num = (seq_num +1) % 2
        check_sum = Create_checksum(packet, seq_num)
        print(f"Packet {count} Checksum: {check_sum}")
        check_sum = check_sum.to_bytes(2, "big")
        header = seq_num.to_bytes(1, "big") + check_sum

        #attach header to packet
        packet_to_send = header + packet

        #send the packet to the server

        Udt_send_packet(packet_to_send)
        #seq_num = (seq_num +1) % 2

        #listen for message back from server
        message_from_server = ""
        message_from_server, serverAddress = client_socket.recvfrom(2048)

        while message_from_server != b"ack":
            #treat NAK and corruption the same
            print("\nThe previous packet had corruption in the data")
            print(f"The packet {count} will be resent")
            #create the header for the packet
            check_sum = Create_checksum(packet, seq_num)
            print(f"Resent Packet Checksum: {check_sum}")
            check_sum = check_sum.to_bytes(2, "big")
            header = seq_num.to_bytes(1, "big") + check_sum

            #attach header to packet
            packet_to_send = header + packet

            #resend the packet to the server
            Udt_send_packet(packet_to_send)
            count += 1

            #wait for server response
            message_from_server = ""
            message_from_server, server_address = client_socket.recvfrom(2048)

            if(message_from_server == b"ack"):
                count - 1
                print(f"Packet {count} sent without corruption in DATA\n")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Completion Time: {elapsed_time: .10f} seconds.")

        #we recieved an ACK we can move forward to our next pack to be processed
        #seq_num = (seq_num +1) % 2 # Using mod to make sure sequence number stays 0/

final_message = b"end"
#encodeFinalMessage = base64.b64encode(finalMessage)
client_socket.sendto(final_message, (server_name, client_port))
print("Packets sent:", count)
print("All packets sent.\nShutting down client...")
client_socket.close()