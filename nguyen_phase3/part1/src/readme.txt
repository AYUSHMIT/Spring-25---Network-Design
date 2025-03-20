Usage Notes
	•	Switching Modes:
            Change the value of SIMULATION_OPTION at the top of each file to test different scenarios. For example, setting SIMULATION_OPTION = 2 in 
            the client simulates ACK bit errors, while setting SIMULATION_OPTION = 3 in the server simulates data packet bit errors.
	•	Testing:
        Start the server script first, then run the client script. The log file (log.txt) will record the events, 
        including any simulated errors and retransmissions.

These complete scripts meet the assignment instructions by implementing the core reliable data transfer functionality over UDP 
and by adding configurable simulation options for various error scenarios. Let me know if you need any further adjustments!