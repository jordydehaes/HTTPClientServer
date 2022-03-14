# Echo server program
import socket

HOST = '127.0.0.1'        # Symbolic name meaning all available interfaces
PORT = 63862                 # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, address = s.accept()
    with conn:
        print('Connected by', address)
        while True:
            data = conn.recv(1024)
            if not data: break
            conn.sendall(data)