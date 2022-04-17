import socket
import threading
from datetime import datetime, timezone

class HTTPServer:

    def __init__(self, ip, port):
        self.ip = ip # The server's IP addr.
        self.port = port # The server's port number.
        self.addr = (ip, port) # The server's addr.
        self.images = ["bombPlanted.jpg", "cryingJordan.jpg", "leoMemeFace.jpg"]
        self.s = self.createSocket() # Instantiate the socket.


    def createSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create an IPv4, TCP socket.
        s.bind(self.addr) # Associate the socket with a network interface and port number. Since we use IPv4, bind expected two values: port and host.
        print(f"[SOCKET CREATED] {self.addr}")
        return s


    def startServer(self):
        self.s.listen() # Enables the server to accept connections.
        print("[LISTENING] Server listening for incoming connections...")
        while True:
            conn, addr = self.s.accept() # Blocks execution and waits for incoming connections.
            thread = threading.Thread(target=self.handleClient, args=(conn, addr)) # Starts a new thread that handles this specific client.
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


    def handleClient(self, conn, addr):
        print(f"[CONNECTION OPENED] {addr} connected.")
        while True:
            try:
                request = conn.recv(2048)
            except:
                print(f"[CONNECTION CLOSED] {addr} disconnected.")
                print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")
                break
            if request != b'':
                requestHTTPMethod = self.getHTTPMethod(request.decode())
                self.handleRequest(request, requestHTTPMethod, conn)


    def getHTTPMethod(self, request):
        httpMethod = request.split()[0]
        return httpMethod


    def handleRequest(self, request, httpMethod, conn):
        if self.validateRequest(request, conn):
            if httpMethod == "GET":
                self.handleGetRequest(request, conn)
            elif httpMethod == "POST":
                self.handlePostRequest(request, conn)
            elif httpMethod == "PUT":
                self.handlePutRequest(request, conn)
            elif httpMethod == "HEAD":
                self.handleHeadRequest(request, conn)


    def validateRequest(self, request, conn):
        if request.find(b"Host:") == -1:
            print("[INVALID REQUEST] Host header not found in headers.")
            self.send400BadRequest(conn)
            return False
        return True

    
    def send400BadRequest(self, conn):
        filePath = 'MyWebPage/400.html'
        file = open(filePath, 'r')
        webPage = file.read()
        lengthWebPage = str(len(webPage))
        headers = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        body = webPage
        conn.send((headers + body).encode())


    def handleGetRequest(self, request, conn):
        end = request.find(b"HTTP/1.1")
        start = request.find(b" ")
        requestedResource = request[start + 1:end - 1]

        if requestedResource == b'/':
            filePath = 'MyWebPage/index.html'
            file = open(filePath, 'r')
            webPage = file.read()
            lengthWebPage = str(len(webPage))
            headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
            body = webPage
            conn.send((headers + body).encode())
            self.checkConnenctionClose(request, conn)
            return
        
        for image in self.images:
            if requestedResource == image.encode():
                
                self.checkCloseConnection(request, conn)
                return


    def checkConnenctionClose(self, request, conn):
        if request.find(b"Connection: close") != -1:
            conn.close()


    def getDateTime(self):
        now = datetime.now(timezone.utc)
        dayName = now.strftime("%A")[0:3]
        format = f"{dayName}, %d %b %Y %H:%M:%S GMT"
        return now.strftime(format)



#httpServer = HTTPServer("localhost", 8000)
#print(httpServer.getDateTime())