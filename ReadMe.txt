EECE 4830-5830 Network Design, Dr. Vinod Vokkarane Programming Project 
Phase 2  Section I: Implement RDT 2.2 over an unreliable UDP channel with bit-errors  

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

Date: 02-21-2025

Description:
This project implements a reliable data transfer (RDT) protocol version 2.2 using UDP sockets in Python. The project includes a graphical user interface (GUI) for sending and receiving files, specifically JPEG images, while displaying the file transfer status and the finite state machine (FSM) state.

Files Submitted:

* client_phase_2.py: This file contains the code for the client application, which sends a JPEG image file to the server using the RDT 2.2 protocol.
* server_phase_2.py: This file contains the code for the server application, which receives the JPEG image file from the client using the RDT 2.2 protocol.
* ui_phase_2.py: This file contains the GUI code for sending and receiving files using the RDT 2.2 protocol.
* file_transfer.py: This file contains the core functions for sending and receiving files using the RDT 2.2 protocol.
* performance_plots.py: This file measures and plots the performance of the file transfer process under different conditions.

Steps to Set Up and Execute the RDT 2.2 Program:

1. Ensure that both the client and server code files are in the same directory.
2. Place a JPEG image file in the same directory as the client code (`client_phase_2.py`).
3. Open two terminals or command prompts.
4. In the first terminal, navigate to the directory containing the server code and run the command `python server_phase_2.py`.
5. In the second terminal, navigate to the directory containing the client code and run the command `python client_phase_2.py`.

The client will send the JPEG image file to the server, and the server will save the received file in the same directory.

Steps to Set Up and Execute the GUI Program:

1. Ensure that the `ui_phase_2.py` and `file_transfer.py` files are in the same directory.
2. Open a terminal or command prompt.
3. Navigate to the directory containing the `ui_phase_2.py` file.
4. Run the command `python ui_phase_2.py`.

The GUI will open, allowing you to send and receive JPEG image files while displaying the FSM state and the transfer status.

Steps to Measure and Plot Performance:

1. Ensure that the `performance_plots.py`, `client_phase_2.py`, `server_phase_2.py`, and `file_transfer.py` files are in the same directory.
2. Open a terminal or command prompt.
3. Navigate to the directory containing the `performance_plots.py` file.
4. Run the command `python performance_plots.py`.

The script will measure the completion time for file transfers under different conditions and plot the results.