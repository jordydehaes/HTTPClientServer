import socket
import threading
from datetime import datetime, timezone

class HTTPServer:

    def __init__(self, ip, port):
        self.ip = ip # The server's IP addr.
        self.port = port # The server's port number.
        self.addr = (ip, port) # The server's addr.
        self.images = ["/bombPlanted.jpg", "/cryingJordan.jpg", "/leoMemeFace.jpg"]
        self.webPages = ["index.html", "page.html", "304.html", "400.html", "404.html", "500.html", "putFile.txt"]
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
                self.get(request, conn)
            elif httpMethod == "HEAD":
                self.head(request, conn)
            elif httpMethod == "POST":
                self.post(request, conn)
            elif httpMethod == "PUT":
                self.put(request, conn)


    def validateRequest(self, request, conn):
        if request.find(b"Host:") == -1:
            print("[INVALID REQUEST] Host header not found in headers.")
            self.sendStatusCode(conn, 400, 'Bad Request')
            return False
        return True

    def sendStatusCode(self, conn, statusCode, status):
        filePath = f'MyWebPage/{statusCode}.html'
        file = open(filePath, 'r')
        webPage = file.read()
        lengthWebPage = str(len(webPage))
        headers = f"HTTP/1.1 {statusCode} {status}\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        body = webPage
        conn.send((headers + body).encode())


    def get(self, request, conn):
        start = request.find(b" ")
        end = request.find(b"HTTP/1.1")
        requestedResource = request[start + 1:end - 1]

        if requestedResource == b'/':
            filePath = 'MyWebPage/index.html'
            file = open(filePath, 'r')
            webPage = file.read()
            lengthWebPage = str(len(webPage))
            headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
            body = webPage
            conn.sendall((headers + body).encode())
            self.checkConnenctionClose(request, conn)
            return
        
        for webPage in self.webPages:
            if requestedResource.decode() == '/' + webPage:
                webPagePath = "MyWebPage/" + webPage
                file = open(webPagePath, 'rb')
                page = file.read()
                pageLength = str(len(page))
                fileExtension = webPage[webPage.find(".") + 1:]
                headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/{fileExtension}\r\nContent-Length: {pageLength}\r\nDate: {self.getDateTime()}\r\n\r\n"
                body = page
                conn.sendall((headers).encode() + body)
                self.checkConnenctionClose(request, conn)
                return

        for image in self.images:
            resourceString = requestedResource.decode()
            if resourceString == image:
                imagePath = "MyWebPage" + image
                file = open(imagePath, 'rb')
                img = file.read()
                lengthImage = str(len(img))
                fileExtension = image[image.find(".") + 1:]
                headers = f"HTTP/1.1 200 OK\r\nContent-Type: image/{fileExtension}\r\nContent-Length: {lengthImage}\r\nDate: {self.getDateTime()}\r\n\r\n"
                body = img
                conn.sendall((headers).encode() + body)
                self.checkConnenctionClose(request, conn)
                return

        self.sendStatusCode(conn, 404, 'Not Found')


    def head(self, request, conn):
        filePath = 'MyWebPage/index.html'
        file = open(filePath, 'r')
        webPage = file.read()
        lengthWebPage = str(len(webPage))
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        conn.send((headers).encode())
        self.checkConnenctionClose(request, conn)


    def put(self, request, conn):
        start = request.find(b" ")
        end = request.find(b"HTTP/1.1")
        requestedResource = request[start + 1:end - 1].decode()
        endHead = request.find(b"\r\n\r\n")
        body = request[endHead + 4:]

        with open("MyWebPage" + requestedResource, 'wb') as f:
            f.write(body)
        headers = f"HTTP/1.1 201 CREATED\r\nContent-Location: {requestedResource}\r\n\r\n"
        conn.send(headers.encode())
        self.checkConnenctionClose(request, conn)


    def post(self, request, conn):
        start = request.find(b" ")
        end = request.find(b"HTTP/1.1")
        requestedResource = request[start + 1:end - 1].decode()
        endHead = request.find(b"\r\n\r\n")
        body = request[endHead + 4:]

        with open("MyWebPage" + requestedResource, 'ab+') as f:
            f.write(body)
            newContent = f.read()
        lengthWebPage = len(newContent)
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        body = newContent
        conn.send(headers.encode() + body)
        self.checkConnenctionClose(request, conn)


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