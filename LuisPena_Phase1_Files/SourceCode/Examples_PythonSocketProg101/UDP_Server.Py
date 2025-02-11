#Notes: 
    #Run Server First: Make sure the server is running before you start the client

#server program begins.

from socket import *                                                    

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)                          #Creates UDP socket
serverSocket.bind(('', serverPort))                                 #bind socket to local port number 12000.
print("The server is ready to receive")

while True:                                                         #Loop forever
    message, clientAddress = serverSocket.recvfrom(2048)            #Read from UDP socket into message, getting client’s address (client IP and port)
    modifiedMessage = message.decode().upper()
    serverSocket.sendto(modifiedMessage.encode(), clientAddress)    #send upper case string back to this client