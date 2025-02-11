Project Title: Phase 1: UDP Client-Server Communication
Author : Luis D. Pena Mateo

Environment
OS: Windows 11
Programming language: Python 3.5
Note: we used visual studio code (VS Code)to write these python scripts. For better results import and execute this code in VS Code.

List of Files:

In folder Phase_1a:

	* UDP_Client.py
		Description: This script implements the UDP client for Phase 1(a). 
		It sends a message to the UDP server and receives the echoed message back.

	* UDP_Server.py
		Description: This script implements the UDP server for Phase 1(a). 
		It receives a message from the UDP client, converts it to uppercase, and sends it back to the client.

In folder Phase_1b:

	*UDP_Client.py
		Description: This script implements the UDP client for Phase 1(b). 
		It sends a BMP file to the UDP server, one packet at a time.

	*UDP_Server.py
		Description: This script implements the UDP server for Phase 1(b).
		It receives the BMP file packets from the UDP client and writes them to a file.

	*input_file:
		Description: BMP file to test the code (Phase_1b)


Instructions: Steps to Set Up and Execute the Programs:

Phase 1(a): Message Transfer

*Run the Server:

	1) Open a terminal or command prompt.
	2) Navigate to the folder Phase_1a directory containing UDP_Server.py
	3) Execute the server script by running: python UDP_Server.py
	4) The server will bind to port 12000 and wait for incoming messages.

*Run the Client:

	1) Open another terminal or command prompt.
	2) Navigate to the folder Phase_1a directory containing UDP_Client.py
	3) Execute the client script by running: python UDP_Client.py
	4) Enter a lowercase sentence when prompted. e.g.: "hello"
	5) The client will send the message to the server, receive the echoed message, and print it in upper case.


Phase 1(b): File Transfer
*Prepare the BMP File:
	1) Place the BMP file (input_file.bpm) to be transferred in the same directory as UDP_Client.py (Phase_1b)
	2) Or alternatively, you could also update the file_path variable in client_part1b.py to match the BMP file name or its explicit.

*Run the Server:

	1) Open a terminal or command prompt.
	2) Navigate to the Phase_1b directory containing UDP_Server.py
	3) Execute the server script by running: python UDP_Server.py
	4) The server will bind to port 12000 and continuously wait for incoming file packets.

*Run the Client:

	1) Open another terminal or command prompt.
	2) Navigate to the directory Phase_1b containing UDP_Client.py
	3) Execute the client script by running: python UDP_Client.py
	4) The client will read the BMP file, break it into packets, and send them to the server.

*Receive the File:
	1) The server will receive the file packets and write them to disk as received_file#.bmp in your python active directory.