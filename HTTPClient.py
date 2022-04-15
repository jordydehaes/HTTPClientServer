import socket
import sys
import os
import bs4 as bs


class HTTPClient:

    def __init__(self, host, port):
        self.host = host.lower() # The server's hostname.
        self.port = int(port) # The port used to reach the host.
        self.s = self.createSocket() # Instantiate the socket and connect with host/port.


    """
    Creates an IPv4, TCP socket and connects to the host using the hostname and port number.

    @return: returns the created socket.
    """
    def createSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create an IPv4, TCP socket.
        print(f"[SOCKET CREATED]")
        s.connect((socket.gethostbyname(self.host), self.port)) # Connect to the host using the host name and port number.
        print(f"[SOCKET CONNECTED] {self.host} {self.port}")
        return s


    """
    Transforms an HTTP string request and transforms it to bytes, then sends it to the server.

    @param request: The HTTP string request.
    """
    def encodeAndSend(self, request):
        bytes = request.encode('utf-8') # Encode string to bytes.
        try:
            self.s.send(bytes) # Send the request to the server.
        except error:
            print(f"Error sending: {error}.")

            
    """
    Sets the host and executes a certain HTTP command based on user input.

    @param host: The host to send the request to.
    @param requestType: String to determine the request type.
    """
    def executeRequest(self, host, requestType):
        self.host = host.lower() # Set the host.
        requestType = requestType.upper()
        if requestType == 'GET': 
            self.get()
        elif requestType == 'POST':
            self.post()
        elif requestType == 'PUT':
            self.put()
        elif requestType == 'HEAD':
            self.head()
        else:
            print('Unknown request type')
            
        
    """
    Retrieves an HTML page from a certain webserver and stores the results locally.
    """
    def get(self):
        request = f'GET / HTTP/1.1\r\nHost: {self.host}\r\n\r\n' # Construct request byte string.
        print(f"[RETRIEVING HTML] GET / HTTP/1.1")
        self.encodeAndSend(request) # Send request to server.
        response = self.rvcChunks() # Read the server reply & store it in 'response'.
        charset = self.findContentType(response)
        self.bodyToString(response, charset) # Pass the byte response to bodyToString
        images = self.scrapeImages()
        if images:
            print(f"[IMAGES FOUND] {images [0:2]}...")
            self.getImages(images)
        self.alterImageSrc()
    

    """
    Retrieves the HEAD response from a certain webserver and stores the results locally.
    """
    def head(self):
        request = f'HEAD / HTTP/1.1\r\nHost: {self.host}\r\nConnection: close\r\n\r\n'
        print(f"[RETRIEVING HTML] HEAD / HTTP/1.1")
        self.encodeAndSend(request)
        response = self.s.recv(1024)
        charset = self.findContentType(response)
        try:
            decodedResponse = response.decode(charset)
            self.writeHTML(decodedResponse, "headers.txt")
        except LookupError:
            decodedResponse = response.decode('utf-8', errors='ignore')
            self.writeHTML(decodedResponse, "headers.txt")



    def post(self):
        body = input("Body: ")
        contenLength = len(body)
        request = f'POST / HTTP/1.1\r\nHost: {self.host}\r\nContent-Length: {contenLength}\r\n\r\n{body}\r\n\r\n'
        print(f"[SENDING POST] POST / HTTP/1.1")
        self.encodeAndSend(request)
        response = self.rvcChunks()
        # try:
        #     self.writeHTML(response.decode('utf-8'), "headers.txt")
        # except Exception as e:
        #     print(f"Error decoding: {e}")


    """
    Retrieves all the chunks from a certain webpage and stores them.

    @return: The request response.
    """
    def rvcChunks(self):
        BUFFERSIZE = 4096
        response = b''
        totalLength = 0
        endOfLineCounter = 0
        contentLength = sys.maxsize
        while True:
            data = self.s.recv(BUFFERSIZE)
            totalLength += len(data)

            if data.find(b"Content-Length:") != -1:
                startPos = data.find(b"Content-Length") # Start position in byte stream where "Content-Length" is found.
                findData = data[startPos:] # Returns the data from the start position in byte stream.
                endPos = findData.find(b"\r\n") # Finds the first occurence of "\r\n" in the byte stream after content length and save its position.
                contentLength = findData[16:endPos].decode() # Gets the content length bytes and decodes it to discover the total content contentLength of HTTP request.

            if data.find(b"\r\n\r\n") != -1:
                endOfLineCounter += 1

            response += data

            if endOfLineCounter >= 2 or totalLength >= int(contentLength): 
                # If second EOL/CRLF (line break) is found, break. (chunked encoding ends with a CRLF)
                # If total received bytes from buffer exceeds or equals (should exceed because of additional bytes fomre the header ietself) actual content length -> break (content-lentgh).
                break
        return response


    def findContentType(self, response):
        charset = ""
        if response.find(b"Content-Type:"):
            startPos = response.find(b"charset=")
            findData = response[startPos:]
            endPos = findData.find(b"\r\n")
            charset = findData[8:endPos].decode()
        return charset


    """
    Creates the file that contains the requested content from a webpage. 

    @param html: The HTML that will be stored in the file.
    @param filename: Name of the file where the requested content is located.
    """
    def writeHTML(self, html, filename):
        myDir = os.getcwd() + "/" + self.host
        if not os.path.exists(myDir):
            os.mkdir(myDir) # Create host folder.
        myFile = open(myDir + "/" + filename, "w") # Write html.
        myFile.write(html)
        myFile.close()


    """
    Removes the HTTP header from the response and converts decodes the byte stream. 

    @param response: The byte response from the HTTP request.
    """
    def bodyToString(self, response, charset):
        bodyBytes = response.split(b'\r\n\r\n')[1] # Remove HTTP header from response.
        try:
            bodyString = bodyBytes.decode(charset) # Decode response to UTF-8.
            self.writeHTML(bodyString, "index.html")
        except LookupError:
            bodyString = bodyBytes.decode('utf-8', errors='ignore') # Decode response to UTF-8.
            self.writeHTML(bodyString, "index.html")


    """
    Looks for all embedded images in the HTML body. 

    @return: An array containing the src of all the images.
    """
    def scrapeImages(self):
        images = []
        text_file = open(self.host + "/" +"index.html", "r")
        soup = bs.BeautifulSoup(text_file,'lxml')
        text_file.close()
        for image in soup.find_all('img'):
            images.append(image.get('src'))
        return images


    """
    Retrieves each image individually from a webpage. 

    @param images: List of all the images names to be retrieved from the webpage.
    """
    def getImages(self, images):
        for image in images:
            request = f'GET /{image} HTTP/1.1\r\nHost: {self.host}\r\n\r\n' # Construct request byte string.
            print(f"[RETRIEVING IMAGE] GET /{image} HTTP/1.1")
            self.encodeAndSend(request)
            response = self.rvcChunks()
            self.writeImage(image, response)

    
    """
    Writes images from the webpage and saves them locally.
    The original folder structure from the webpage is preserved. 

    @param imageName: Name of an individual image.
    @param response: The response that contains the image.
    """
    def writeImage(self, imageName, response):
        image = response.split(b'\r\n\r\n')[1]
        if imageName.startswith('/'):
         imageName = imageName[1:]
        if imageName.find('/'):
            os.makedirs(os.getcwd() + "/" + self.host + "/" + os.path.dirname(imageName), exist_ok=True)
            with open(os.getcwd() + "/" + self.host + "/" + imageName, "wb") as f:
                f.write(image)
        else:
            with open(os.getcwd() + "/" + self.host + "/" + imageName, "wb") as f:
                f.write(image)


    """
    Alters the src path from the images in the body so the stored webpage loads the images correctly.
    """
    def alterImageSrc(self):
        body = open(os.getcwd() + "/" + self.host + "/" + "index.html", "r")
        soup = bs.BeautifulSoup(body, 'lxml')
        images = soup.find_all("img")
        for image in images:
            src = image.get('src')
            if src[0] == '/':
                image['src'] = src[1:]
        with open(os.getcwd() + "/" + self.host + "/" + "index.html", "w") as f:
             f.write(str(soup))