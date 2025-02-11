#Notes: 
    #Run Server First: Make sure the server is running before you start the client.

#server program begins.

from socket import *

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)                 #create TCP welcoming socket.
serverSocket.bind(('', serverPort))
serverSocket.listen(1)                                      #server begins listening for  incoming TCP requests
print('The server is ready to receive')
while True:                                                 #loop forever
    connectionSocket, addr = serverSocket.accept()          #server waits on accept() for incoming requests, 
                                                            #new socket created on return

    sentence = connectionSocket.recv(1024).decode()         #read bytes from socket (but not address as in UDP)
    capitalizedSentence = sentence.upper()
    connectionSocket.send(capitalizedSentence.encode())

    connectionSocket.close()                               #close connection to this client (but not welcoming socket)


