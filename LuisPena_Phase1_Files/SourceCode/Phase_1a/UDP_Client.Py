#Notes:
    #Run Server First: Make sure the server is running before you start the client
'''
Based on example code provided in "Python Socket Programming 101 - Python.pptx" on Blackboard
'''

#Client program begins.

from socket import *                                                #include python library

serverName = 'localhost'                                            #using 'localhost' since I'm running both the server and client on the same machine.
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)                          #Create UDP socket for Server 

message = input('Input lowercase sentence (e.g: "hello"):')         #Get User keyboard input
clientSocket.sendto(message.encode(), (serverName, serverPort))     #Attach server name, port message; send into socket.

modifiedMessage, serverAddress = clientSocket.recvfrom(2048)        #Read reply characters from socket into string.
print(modifiedMessage.decode())                                     #print out received string and close socket                                 
clientSocket.close()