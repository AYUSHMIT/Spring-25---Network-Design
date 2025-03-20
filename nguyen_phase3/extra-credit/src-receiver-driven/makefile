.PHONY: live exp clean

live:
	@echo "Starting receiver-driven server in live mode..."
	python3 server_rd.py received_file.jpg 127.0.0.1 10 1 > receiver.log 2>&1 &
	@sleep 2
	@echo "Starting receiver-driven GUI..."
	python3 gui.py > gui.log 2>&1 &
	@sleep 2
	@echo "Starting receiver-driven client..."
	python3 client_rd.py image.jpg 127.0.0.1 10 1

exp:
	@echo "Starting receiver-driven server for experiments..."
	python3 server_rd.py received_file.jpg 127.0.0.1 10 1 > receiver.log 2>&1 &
	@sleep 2
	@echo "Starting experiments..."
	python3 graph_experiment.py > experiment.log 2>&1
	@sleep 2

clean:
	@echo "Killing receiver-driven server, GUI, and client processes..."
	pkill -f server_rd.py || true
	pkill -f graph_experiment.py || true
	pkill -f gui.py || true
	pkill -f client_rd.py || true