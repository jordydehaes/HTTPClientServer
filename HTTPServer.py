import socket
import threading
from datetime import datetime, timezone

class HTTPServer:

    def __init__(self, ip, port):
        self.ip = ip # The server' IP addr.
        self.port = port # The server' port number.
        self.addr = (ip, port) # The server' addr.
        self.images = [ "/bombPlanted.jpg", "/cryingJordan.jpg", "/leoMemeFace.jpg" ]
        self.webPages = ["index.html", "page.html", "304.html", "400.html", "404.html", "500.html" ]
        self.ifModSince = { "/index.html": "Mon, 18 Apr 2022 11:07:33 GMT",
                            "/page.html": "Mon, 18 Apr 2022 11:07:33 GMT",
                            "/bombPlanted.jpg": "Mon, 18 Apr 2022 11:07:33 GMT",
                            "/leoMemeFace.jpg": "Mon, 18 Apr 2022 11:07:33 GMT",
                            "/cryingJordan.jpg": "Mon, 18 Apr 2022 11:07:33 GMT" }
        self.s = self.createSocket() # Instantiate the socket.


    """
    Creates an IPv4, TCP socket and binds to an ip and port number.

    @return: Returns the created socket.
    """
    def createSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create an IPv4, TCP socket.
        s.bind(self.addr) # Associate the socket with a network interface and port number. Since we use IPv4, bind expected two values: port and host.
        print(f"[SOCKET CREATED] {self.addr}")
        return s


    """
    Server starts listening for incoming connections, allocates a thread per new connection.
    """
    def startServer(self):
        self.s.listen() # Enables the server to accept connections.
        print("[LISTENING] Server listening for incoming connections...")
        while True:
            conn, addr = self.s.accept() # Blocks execution and waits for incoming connections.
            thread = threading.Thread(target=self.handleClient, args=(conn, addr)) # Starts a new thread that handles this specific client.
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


    """
    Handles a new client connected to the server by receiving/handling its requests.

    @param conn: The connection between client and server.
    @param addr: The address and port number from the client.
    """
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


    """
    Determines the HTTP method used from a request.

    @param request: The incoming request from a client.
    @return: Returns the HTTP method from the incoming request.
    """
    def getHTTPMethod(self, request):
        httpMethod = request.split()[0]
        return httpMethod


    """
    Checks the HTTP method and handles the request accordingly..

    @param request: The incoming request from a client.
    @param htttpMethod: An HTTP method such as GET, HEAD, ...
    @param conn: The connection between client and server.
    """
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


    """
    Checks if the request is valid, if there is no host field return a 400.

    @param request: The incoming request from a client.
    @param conn: The connection between client and server.
    @return: Returns True if the request is valid, false if it's not.
    """
    def validateRequest(self, request, conn):
        if request.find(b"Host:") == -1:
            print("[INVALID REQUEST] Host header not found in headers.")
            self.sendStatusCode(conn, 400, 'Bad Request')
            return False
        return True


    """
    Sends a response with a certain status code and the matching HTML body.

    @param conn: The connection between client and server.
    @param statusCode: The status code for the response.
    @param status: The status of the status code.
    """
    def sendStatusCode(self, conn, statusCode, status):
        filePath = f'MyWebPage/{statusCode}.html'
        file = open(filePath, 'r')
        webPage = file.read()
        lengthWebPage = str(len(webPage))
        headers = f"HTTP/1.1 {statusCode} {status}\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        body = webPage
        conn.send((headers + body).encode())


    """
    Handles get requests and returns the requested resource from the server.
    Also checks the If-Modified-Since header, returns a 404 if the resource doesn't exist.
    Checks if the connection needs to be closed after the response has been delivered.

    @param request: The incoming request from a client.
    @param conn: The connection between client and server.
    """
    def get(self, request, conn):
        start = request.find(b" ")
        end = request.find(b"HTTP/1.1")
        requestedResource = request[start + 1:end - 1]

        ifModSince = request.find(b"If-Modified-Since:")
        if ifModSince != -1:
            data = request[ifModSince:]
            end = data.find(b"\r\n")

            stringRequestedResource = requestedResource.decode()
            if stringRequestedResource in self.ifModSince:
                dateRequest = data[19:end].decode()
                dateServer = self.ifModSince[stringRequestedResource]

                if not self.checkIfModSince(dateServer, dateRequest):
                    self.sendStatusCode(conn, 304, 'Not Modified')
                    self.checkConnenctionClose(request, conn)
                    return
            else:
                self.sendStatusCode(conn, 404, 'Not Found')
                return

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


    """
    Handles head requests and returns the headers from a specific web page.
    Also checks the If-Modified-Since header, returns a 404 if the resource doesn't exist.
    Checks if the connection needs to be closed after the response has been delivered.

    @param request: The incoming request from a client.
    @param conn: The connection between client and server.
    """
    def head(self, request, conn):
        ifModSince = request.find(b"If-Modified-Since:")
        if ifModSince != -1:
            data = request[ifModSince:]
            end = data.find(b"\r\n")

            stringRequestedResource = "/index.html"
            if stringRequestedResource in self.ifModSince:
                dateRequest = data[19:end].decode()
                dateServer = self.ifModSince[stringRequestedResource]

                if not self.checkIfModSince(dateServer, dateRequest):
                    self.sendStatusCode(conn, 304, 'Not Modified')
                    self.checkConnenctionClose(request, conn)
                    return
            else:
                self.sendStatusCode(conn, 404, 'Not Found')
                return
        filePath = 'MyWebPage/index.html'
        file = open(filePath, 'r')
        webPage = file.read()
        lengthWebPage = str(len(webPage))
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        conn.send((headers).encode())
        self.checkConnenctionClose(request, conn)


    """
    Handles put requests and returns a 201 if the new file has been created on the server.
    If the file already has been created it overwrites its content.
    Checks if the connection needs to be closed after the response has been delivered.

    @param request: The incoming request from a client.
    @param conn: The connection between client and server.
    """
    def put(self, request, conn):
        start = request.find(b" ")
        end = request.find(b"HTTP/1.1")
        requestedResource = request[start + 1:end - 1].decode()
        body = request.split(b"\r\n\r\n")[1]
        endBody = body.find(b"\r\n\r\n")
        finalBody = body[:endBody]

        with open("MyWebPage" + requestedResource, 'wb') as f:
            f.write(finalBody)
        headers = f"HTTP/1.1 201 CREATED\r\nContent-Location: {requestedResource}\r\n\r\n"
        conn.send(headers.encode())
        self.checkConnenctionClose(request, conn)


    """
    Handles post requests and returns a 200 if the request succeeds.
    If the file already has been created it the new content to the current content of the file.
    If the file doesn't exist yet it will create it.
    Checks if the connection needs to be closed after the response has been delivered.

    @param request: The incoming request from a client.
    @param conn: The connection between client and server.
    """
    def post(self, request, conn):
        start = request.find(b" ")
        end = request.find(b"HTTP/1.1")
        requestedResource = request[start + 1:end - 1].decode()
        body = request.split(b"\r\n\r\n")[1]
        endBody = body.find(b"\r\n\r\n")
        finalBody = body[:endBody]

        with open("MyWebPage" + requestedResource, 'ab+') as f:
            f.write(finalBody)
        with open("MyWebPage" + requestedResource, 'rb') as f:
            newContent = f.read()
        lengthWebPage = len(newContent)
        headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {lengthWebPage}\r\nDate: {self.getDateTime()}\r\n\r\n"
        finalBody = newContent
        conn.send(headers.encode() + finalBody)
        self.checkConnenctionClose(request, conn)


    """
    Compares the date from the If-Modified-Since header with the date on the server.
    If the date on the server is more recent than the one from the request it will return True otherwise False.

    @param dateServer: The last modifified date time from the specific resource on the webserver.
    @param dateRequest: The date time included in the request to the server.
    @return: Returns True or False based on the comparison of the two arguments.
    """
    def checkIfModSince(self, dateServer, dateRequest):
        monthsDic = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
        serverModified = dateServer.split()
        dateRequest = dateRequest.split()
        serverDateTimeMod = datetime(int(serverModified[3]), monthsDic[serverModified[2]], int(serverModified[1]))
        requestDateTime = datetime(int(dateRequest[3]), monthsDic[dateRequest[2]], int(dateRequest[1]))
        if requestDateTime > serverDateTimeMod:
            return False
        if requestDateTime < serverDateTimeMod:
            return True
        if dateRequest[4] < serverModified[4]:
            return True
        return False


    """
    Checks if the request has the "Connection: close" header, if so it closes the connection with the client after responding.

    @param request: The incoming request from a client.
    @param conn: The connection between client and server.
    """
    def checkConnenctionClose(self, request, conn):
        if request.find(b"Connection: close") != -1:
            conn.close()
            print("[CONNECTION CLOSED] A client has disconnected.")
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")


    """
    Formats the current date time into the required format for the "Date" header to send along with the response.

    @return: Returns the current date time in the required format.
    """
    def getDateTime(self):
        now = datetime.now(timezone.utc)
        dayName = now.strftime("%A")[0:3]
        format = f"{dayName}, %d %b %Y %H:%M:%S GMT"
        return now.strftime(format)