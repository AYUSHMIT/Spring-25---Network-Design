import socket
import random

server_port = 12000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("",server_port))
print("The server is ready to receive.\n")

image_reconstruct = []

def Create_checksum(data, sequence_number): 
    return (sum(data) + sequence_number) % 65536

def Corrupt_data(data, seq_num):
    percent_check = random.randint(0,9)
    if percent_check !=0:
        # simulate a checksum error 10% of the time
        return Create_checksum(data, seq_num)
    else:
        # simulate a bit error in the checksum
        data_int = int.from_bytes(data, "big")
        num_bits = data_int.bit_length()
        num_bytes = (num_bits + 7) // 8
        bit = 1 << random.randint(0, num_bits-1)
        data_int = data_int ^ bit
        data = data_int.to_bytes(num_bytes, "big")
        calculated_checksum = Create_checksum(data, seq_num)
        return calculated_checksum

#listen for client to tell us what option we have selected
option_one_chose = False
while True:
    message_from_client, client_address = server_socket.recvfrom(2048)
    if(message_from_client == b"op1"):
        option_one_chose = True
        break
    else:
        option_one_chose = False
        break

packet_num = 0
expected_seg_num = 0
input_coount = 0
while True: # continuous loop to read data from the client
    packet, client_address = server_socket.recvfrom(2048)
    packet_num +=1
    print(f"Waiting on packet {packet_num}...")
    print(option_one_chose)
    # decode our packet from the client
    #decodedPacket = base64.b64decode(packet)

    if packet == b"end":
        print("Transmisison finished")
        break
    
    # extract the sequence number and checksum from the packet
    seq_num = packet[0]
    checksum = packet[1:3]
    data = packet[3:]
    
    print("sent seq number: ", seq_num)
    print("expected seq number: ", expected_seg_num)
    if(option_one_chose == True):
        calculated_checksum = Create_checksum(data, seq_num)
    else:
        calculated_checksum = Corrupt_data(data, seq_num)
        
    #if option 1:
        #calculatedChecksum = Create_checksum(data, seqNum)
    #else:
        #calculatedChecksum = Corrupt_data(data, seqNum)
        
    
    checksum = int.from_bytes(checksum, "big")
    # calculate the checksum of the data portion of the packet
    #data = Corrupt_data(data, seqNum)

    #Keep on Danny side for debug
    #calculated_checksum = Corrupt_data(data, seq_num)
    #calculatedChecksum = Create_checksum(data, seqNum)
    #DEBUG END

    # check the checksum with our incoming packet, if there is a mismatch we need to call for
    # the packet to be resent
    # we do not proceed forward until a succesful packet is recieved
    if(calculated_checksum != checksum):
        print("Checksum from client: ", checksum)
        print("Checksum produced by the server: ", calculated_checksum)
        print("The packet recieved has a checksum mismatch, requesting a new packet")
        message = b"nak"
        server_socket.sendto(message, client_address)
        print("New packet request sent\n")
    else:
        #if our sequence don't match incoming to expected, after passing the checksum then we know
        #the client is asking for the ack back to move forward.

        #if the sequence numbers are different after passing the checksum we know that we can process the
        #packet and move forward
        print("before the condition")
        if(seq_num != expected_seg_num):
            #resend ACK
            print("Sequence numbers do not match, ACK must be resent\n")
            message = b"ack"
            server_socket.sendto(message, client_address)
        else:
            #we know we can move forward as expected sequence number matches the current sequence number
            #now we will prepare for the next packet sequence number
            print("Seq match and Checksum match")
            if(expected_seg_num == 0):
                expected_seg_num = 1
            else:
                expected_seg_num = 0

            # add the packet and sequence number to our imageReconstruct list
            #image_reconstruct.append((seq_num, data))
            input_coount += 1
            print("packets added to image: ", input_coount)
            image_reconstruct.append((data))

            # print out the packet and sequence number
            print(f"Packet {packet_num} has been received from the client.")
            print("Checksum that came with the packet: ", checksum)
            print("Checksums calculated in server: ", Create_checksum(data, seq_num))
            print("\n")
            # tell the client that we have processed the packet
            message = b"ack"
            server_socket.sendto(message, client_address)


#put together our fixed image
print("Now process the packets and construct the new image file\n")
with open("received_image.jpg", "wb") as file:
    for packet in image_reconstruct:
        file.write(packet)

server_socket.close()