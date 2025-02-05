EECE 4830-5830 Network Design, Dr. Vinod Vokkarane Programming Project 
Phase 1  File Transfer between a UDP Client and a UDP Server  

Group members:
Ayush Pandey
Parthaw Goswami
Luis Daniel Peña Mateo
Joseph Nguyen

Environment 
OS used for our code: Windows 
Name of the programming language used: Python
Version of programming language: Python 3.12.6
IDE: Visual Studio 2022

Date: 02-05-2025

Description:
This project implements a file transfer system using UDP sockets and the RDT 1.0 protocol. The system consists of a client and a server that communicate over a network to transfer a BMP image file.

Files Submitted:

* Client.py: This file contains the code for the client application, which sends a "HELLO" message to the server and receives an echoed response.
* Server.py: This file contains the code for the server application, which listens for messages from the client, echoes them back, and processes them (e.g., converts to uppercase).
* client_rdt.py: This file contains the code for the client application, which sends a BMP image file to the server using the RDT 1.0 protocol.
* server_rdt.py: This file contains the code for the server application, which receives the BMP image file from the client using the RDT 1.0 protocol.
* image.bmp: This is a sample BMP image file used for testing the file transfer functionality.

Steps to Set Up and Execute the Program:

1. Ensure that both the client and server code files are in the same directory.
2. Place the `image.bmp` file in the same directory as the client code (`client_rdt.py`).
3. Open two terminals or command prompts.
4. In the first terminal, navigate to the directory containing the server code and run the command `python server_rdt.py`.
5. In the second terminal, navigate to the directory containing the client code and run the command `python client_rdt.py`.

The client will send the `image.bmp` file to the server, and the server will save the received file as `received_image.bmp` in the same directory.


