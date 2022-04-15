import sys
import socket
import threading
import types

class HTTPServer:

    def __init__(self, ip, port):
        self.ip = ip # The server's IP addr.
        self.port = port # The server's port number.
        self.addr = (ip, port) # The server's addr.
        self.s = self.createSocket() # Instantiate the socket and start listening for connections.


    def createSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create an IPv4, TCP socket.
        s.bind(self.addr) # Associate the socket with a network interface and port number. Since we use IPv4, bind expected two values: port and host.
        print(f"[SOCKET CREATED] {self.addr}")
        return s


    def startServer(self):
        self.s.listen() # Enables the server to accept connections.
        print("[LISTENING] Server listening for incoming connections...\r\n")
        while True:
            conn, addr = self.s.accept() # Blocks execution and waits for incoming connections.
            thread = threading.Thread(target=self.handleClient, args=(conn, addr)) # Starts a new thread that handles this specific client.
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}\r\n")


    def handleClient(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.\r\n")
        while True:
            try:
                request = conn.recv(1024)
            except:
                print(f"[CONNECTION CLOSED] {addr} disconnected.")
                print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}\r\n")
                break
            print(request.decode())
            # type = self.getRequestType(request.decode())
            # self.handleRequest(request, type, conn)

    
    def handleRequest(self):


    def 
