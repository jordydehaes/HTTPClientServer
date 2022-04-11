import sys
import socket
import selectors
import types

HOST = "127.0.0.1"        # Localhost interface (loopback)
PORT = 4570               # Arbitrary non-privileged port

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # we pass AF_INET and SOCK_STREAM, these are to specify we will be usinf IPv4 and TCP.
    s.bind((HOST, PORT)) # Associate the socket with a network interface and port number. Since we use IPv4, bind expected two values: port and host.
    s.listen() # Enables the server to accept connections.
    print("# Server waiting for incoming connections...")
    conn, address = s.accept() # Blocks execution and waits for incoming connections.
    with conn:
        print(f"Connected by: {address}")
        while True:
            data = conn.recv(4096)
            print(data.decode('utf-8'))
            if not data: 
                break
            conn.sendall(b'HTTP/1.0 200 OK\n\n<h1>Hello World</h1>')