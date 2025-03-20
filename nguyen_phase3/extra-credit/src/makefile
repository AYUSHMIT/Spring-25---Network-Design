.PHONY: live exp clean

live:
	@echo "Starting server in live mode..."
	python3 server.py received_file.jpg sender_driven 10 1 > server.log 2>&1 &
	@sleep 2
	@echo "Starting GUI..."
	python3 gui.py > gui.log 2>&1 &
	@sleep 2
	@echo "Starting live client..."
	python3 client.py image.bmp 127.0.0.1 sender_driven 10 1

exp:
	@echo "Starting server for experiments (ensure you run experiments for each option separately if needed)..."
	python3 server.py received_file.jpg sender_driven 10 1 > server.log 2>&1 &
	@sleep 2
	@echo "Starting experiments..."
	python3 experiment.py > experiment.log 2>&1
	@sleep 2

clean:
	@echo "Killing server, GUI, and experiment processes..."
	pkill -f server.py
	pkill -f experiment.py
	pkill -f gui.py