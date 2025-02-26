# Image Server and Client-Server UDP Communication

## Overview

This project implements an image transfer system using UDP communication between a client and a server. The system allows the transmission of image files while simulating network issues such as packet corruption and acknowledgment (ACK) corruption.

## Features

- **Reliable UDP Transmission**: Implements a stop-and-wait protocol to ensure reliable transmission.
- **Checksum Verification**: Uses checksum validation to detect corrupted packets.
- **Packet Corruption Simulation**: Can introduce errors in packets to test robustness.
- **ACK Corruption Simulation**: Corrupts ACK messages to simulate real-world network conditions.
- **Three Transmission Modes**:
  1. **No loss/bit-errors** (Standard reliable transmission)
  2. **ACK packet bit-error** (Simulates ACK corruption)
  3. **Data packet bit-error** (Simulates data corruption)

## Components

### 1. Image Server (`imageserver.py`)

- Listens for incoming image packets from the client.
- Validates received packets using sequence numbers and checksums.
- Requests retransmission if errors are detected.
- Reconstructs and saves the received image.

### 2. Client Server (`clientserver.py`)

- Reads and splits an image file into packets.
- Attaches sequence numbers and checksums before sending packets.
- Waits for acknowledgment (ACK) from the server before proceeding.
- Implements error simulation based on user-selected mode.

## How It Works

1. **Start the Image Server**

   ```sh
   python imageserver.py
   ```

   The server will start listening on port `12000` for incoming packets.

2. **Run the Client Server**

   ```sh
   python clientserver.py
   ```

   The client will prompt for an error simulation mode:

   - `Option 1`: No errors
   - `Option 2`: ACK corruption
   - `Option 3`: Data corruption

3. **Select an Image File**

   - The client reads the image file (default: `FattestCatEver.jpg`).
   - Splits it into 1024-byte packets.
   - Sends packets to the server using a stop-and-wait approach.

4. **Packet Transmission & Error Handling**

   - The server validates packets using sequence numbers and checksums.
   - If an error is detected, the server requests retransmission (`NAK` message).
   - If packets are correctly received, the server sends an `ACK` message.

5. **Image Reconstruction**

   - The server reconstructs the received image from packets.
   - Saves the file as `received_image.jpg`.

## Dependencies

- Python 3.x
- Socket Module (Standard Python Library)

## Notes

- Ensure that both server and client run on the same network.
- The client must use the correct hostname or IP address of the server.
- The project can be extended to use TCP for more reliable transmission.

## Future Enhancements

- Implementing a **Selective Repeat ARQ** mechanism.
- Enhancing **error detection and correction** mechanisms.
- Supporting **multi-client parallel image transfers**.

## Authors

- Developed for network reliability simulation in **UDP-based image transmission**.

---

This project is intended for educational purposes and simulation of network behavior in unreliable environments.

