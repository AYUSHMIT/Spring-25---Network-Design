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
