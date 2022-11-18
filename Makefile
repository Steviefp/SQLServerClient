server: server.py
	python server.py

client: client.py
	python client.py

clean:
    rm -rf __pycache__