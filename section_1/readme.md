# Go-Back-N BMP Transfer Protocol

This project implements the Go-Back-N protocol for transferring BMP image files over UDP. It includes features for packet creation, sequence number management, checksum calculation, and handling various data transfer scenarios such as packet loss and bit errors.

## Project Structure

```
go-back-n-bmp-transfer
├── src
│   ├── __init__.py          # Marks the src directory as a Python package
│   ├── go_back_n.py         # Core implementation of the Go-Back-N protocol
│   ├── sender.py            # Sender side implementation for BMP file transfer
│   ├── receiver.py          # Receiver side implementation for BMP file transfer
│   └── utils.py             # Utility functions for the project
├── tests
│   ├── __init__.py          # Marks the tests directory as a Python package
│   ├── test_go_back_n.py    # Unit tests for Go-Back-N protocol functions
│   ├── test_sender.py       # Unit tests for sender implementation
│   └── test_receiver.py     # Unit tests for receiver implementation
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Features

- **Packet Creation**: Constructs packets with sequence numbers, checksums, and data.
- **Sequence Number Management**: Manages the sequence numbers for packets to ensure correct order.
- **Checksum Calculation**: Implements a checksum mechanism to verify data integrity.
- **ACK Handling**: Sends and receives acknowledgments for successfully received packets.
- **Data Transfer Scenarios**: Simulates packet loss and bit errors to test the robustness of the protocol.

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/AYUSHMIT/Spring-25---Network-Design/tree/phase_4/section_1
   cd go-back-n-bmp-transfer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the sender and receiver scripts to transfer BMP files.

## Usage Example

To transfer a BMP image file, run the receiver in one terminal:
```
python -m section_1.src.receiver <host> <port> <output_file>

e.g: python -m section_1.src.receiver received.bmp
```

Then, in another terminal, run the sender:
```
python -m section_1.src.sender <host> <port> <input_file>

e.g: python -m section_1.src.sender section_1\src\example.bmp
```

Replace `<host>`, `<port>`, `<output_file>`, and `<input_file>` with appropriate values.

## Testing

To run the tests, use:
```
pytest tests/
```

This will execute all unit tests for the Go-Back-N protocol implementation, ensuring that the functionality works as expected.