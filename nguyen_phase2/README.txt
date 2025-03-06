EECE 4830-5830 Network Design, Dr. Vinod Vokkarane  
Programming Project - Phase 2  

Implement RDT 2.2 over an unreliable UDP channel with bit-errors  

Group Members:  
Ayush Pandey  
Parthaw Goswami  
Luis Daniel Peña Mateo  
Joseph Nguyen  

Environment:  
OS used for our code: MacOS  
Name of the programming language used: Python  
Version of programming language: Python 3.12.6  
IDE: Visual Studio Code  

Date: 02-23-2025  

---

## **Project Description**  
This project implements a **basic UDP client-server file transfer** system with **error handling** using **Reliable Data Transfer (RDT) 2.2**. It is built over an **unreliable UDP channel** that can introduce **bit errors in packets and ACKs**.

### **🔹 Phase 2 - RDT 2.2 (Reliable UDP File Transfer with Error Handling)**
1. **Checksum-Based Error Detection**  
   - Each packet includes a **1-byte checksum** to detect corruption.
   - The **server calculates a checksum on received packets** and **compares it to the sent checksum**.
   - If a mismatch occurs, the packet is discarded.

2. **Handling ACK Corruption**  
   - The **server sends an ACK for each valid packet**.
   - To simulate **ACK corruption**, we introduce a **20% probability of sending an incorrect ACK**.
   - If the **client receives a corrupted ACK**, it resends the last packet.

3. **Retransmission for Lost or Corrupt Packets**  
   - The **client has a timeout mechanism** (`settimeout(0.3)`) to **detect lost ACKs**.
   - If an ACK is not received, or is incorrect, the **client resends the last packet**.

4. **Performance Measurement with Different Error Rates**  
   - The program was run at **incremental error rates (0% to 60%)**.
   - A graph was generated showing how **completion time increases with error rate**.
   - The observed results align with expected **UDP retransmission behavior**.

---

## **Files Submitted:**  

* `client.py` - Implements the **UDP client** for **Phase 2**, including **checksum validation and retransmissions**.  
* `server.py` - Implements the **UDP server** for **Phase 2**, handling **ACK corruption and file reassembly**.  
* `performance_plot.png` - The **graph showing Completion Time vs. Error Rate**. 
* `plot.py` - The **This creates the graph for the completion times for 3 options**. 

For each scenario where there was no/loss error, ACK bit error, and Data packet error. We have checked with no Loss/error by 
adding if there was a "Corrupt" message in the log when sending or receiving. For Ack bit Error, we had checked by introducing 
intentional ACK corruption by flipping a bit acknowledgment number, then the sender logs a mismatch ACK and retransmits the last packet and 
shown in the logs. For Data packet Error scenario, we stimulated bit errors in the received data by flipping bits in received packets, 
the receiver detects checksum mismatches and requests retransmission by sending the last ACK and the sender resends the packet until it is correctly 
received as seen in the Logs. 

To enhance the efficiency and usability of the RDT 2.2 implementation, several advanced features were integrated, 
including multi-threading, GUI visualization, adaptive timeout mechanisms, and CRC-16 error detection. These improvements 
optimize the protocol by reducing transmission delays, improving error handling, and providing real-time monitoring of the
data transfer process. Each enhancement was thoroughly tested to compare performance improvements and ensure
correct functionality under different network conditions.

One of the major improvements was the multi-threaded RDT 2.2 implementation. In the client, a dedicated sending thread continuously transmits data packets, 
while a separate listener thread simultaneously waits for and processes ACKs. Similarly, on the server side, a processing thread was created to handle incoming
 packets and verify their checksum, while a response thread was responsible for sending ACKs back to the sender. This modification significantly reduced 
 transmission time, as data could be sent and acknowledged in parallel instead of waiting for each acknowledgment sequentially. Testing was conducted by 
 comparing total transmission times and analyzing log entries in log.txt for single-threaded vs. multi-threaded runs. The results confirmed that the 
 multi-threaded implementation improves efficiency by reducing idle time and enhancing network performance.

To further improve usability, a high-quality PyQt6-based GUI was developed to visualize the file transfer process. The GUI includes a real-time progress bar,
an FSM (Finite State Machine) visualization that updates as packets are sent and received, and a live image preview of the received file. This enhancement
not only improves the user experience by providing immediate feedback on the transmission status but also aids in debugging by dynamically displaying
packet states. The GUI was tested in various error-handling scenarios, such as packet loss and corruption, to ensure that it accurately reflected 
transmission progress. By implementing this interface, users can now monitor file transfer operations more intuitively and detect potential transmission issues in real time.

Another significant enhancement was the adaptive timeout mechanism, which dynamically adjusts the retransmission timer based on observed network delays. 
Instead of using a static timeout value, the system monitors network latency and adjusts the timeout to prevent unnecessary retransmissions. 
This feature was tested by comparing the performance of a static timeout vs. an adaptive timeout across multiple runs, recording the number of 
retransmissions in each case. The results showed that adaptive timeouts reduce unnecessary retransmissions and improve overall transmission efficiency
 by preventing premature resends and network congestion.

Lastly, CRC-16 error detection was integrated to replace the previous XOR checksum method, improving the protocol’s ability to detect corrupted packets. 
CRC-16, which uses polynomial 0x8005, provides a more robust error-checking mechanism, allowing it to catch more complex errors that XOR checksum might miss. 
Testing was conducted by comparing CRC-16 and XOR checksum in terms of error detection accuracy, processing time, and the number of retransmissions required for 
successful delivery. The findings indicated that CRC-16 detects a significantly higher percentage of errors while slightly increasing processing time. However, 
the reduction in retransmissions due to improved error detection resulted in better overall transmission efficiency.

(Also Reference The performance-Report.pdf for further reasoning)
>>>>>>> Stashed changes


---

## **Steps to Set Up and Execute the Program**  

### **🔹 Running Phase 2**  
1. **Start the server** (First Terminal):  
   ```bash
   python3 server.py
   NEW TERMINAL
   python3 client.py

2. **Run the client/server.py with the increment with 5% write down completion times. (In the while loop)**

3. **After running the client/server with incremental percentages and plug in completion times to calculate graphs**
   ```bash
   python3 plot.py
