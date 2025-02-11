#Notes: 
    #Run Server First: Make sure the server is running before you start the client

#including python libraries
from socket import *
#End Python libraries

#function definitions
def make_packet(file_path, packet_size=1024):
    packets = []
    with open(file_path, "rb") as f:
        file_data = f.read()
        for i in range(0, len(file_data), packet_size):
            packets.append(file_data[i:i+packet_size])
    return packets

#End function definitions

#Client program begins.
print("Loading BMP image...")

# Replace with the actual name of your BMP file
file_path = "input_file.bmp"   #Note: this use your working directory. for explicit path comment this line and use path format below

#or

#example of general file_path
#file_path = r"C:\Users\Luis D. Pena Mateo\OneDrive\Desktop\Spring2025\Network\Project\Phase_1\SourceCode\Phase_1b\ImageFile.bmp"

'''
Note: use one path format or the other, #comment the unusedone
'''
print("parsing the image file and breaking it down to several packets...")  #breaking it down to several packets
packets = make_packet(file_path)
print("parsing complete.")

print("Communication begins...")

serverName = 'localhost'                                            #using 'localhost' since I'm running both the server and client on the same machine.
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)                          #Create UDP socket for Server 

print("Sending packages:")
for packet in packets:
    clientSocket.sendto(packet, (serverName, serverPort))           #Attach server name, port message; send into socket.

print("File transfer complete.")
                               
clientSocket.close()