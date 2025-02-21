# RDT 2.2 File Transfer

This project implements a reliable data transfer (RDT) protocol version 2.2 using UDP sockets in Python. The project includes a graphical user interface (GUI) for sending and receiving files, specifically JPEG images, while displaying the file transfer status and the finite state machine (FSM) state.

## Features

- Send and receive JPEG image files using the RDT 2.2 protocol.
- Display the FSM state during file transfer.
- Show the transfer time and display the transferred image.
- Handle packet loss and errors using sequence numbers and checksums.

## Requirements

- Python 3.x
- Tkinter (for GUI)
- Pillow (for image processing)
- Matplotlib (for plotting performance, if needed)

## Installation

1. Clone the repository or download the source code.
2. Install the required Python packages using pip:

```sh
pip install pillow matplotlib