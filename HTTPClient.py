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
        except Exception as e:
            print(f"Error sending: {e}")

            
    """
    Sets the host and executes a certain HTTP command based on user input.

    @param host: The host to send the request to.
    @param requestType: String to determine the request type.
    """
    def executeRequest(self, host, requestType, resource="", body=""):
        self.host = host.lower() # Set the host.
        requestType = requestType.upper()
        if requestType == 'GET': 
            self.get(resource)
        elif requestType == 'POST':
            self.post(resource, body)
        elif requestType == 'PUT':
            self.put(resource, body)
        elif requestType == 'HEAD':
            self.head()
        else:
            print('Unknown request type')
            
        
    """
    Retrieves an HTML page from a certain webserver and stores the results locally.

    @param resource: What specific resource to retrieve from the webserver, if nothing is provided, retrieves the root.
    """
    def get(self, resource=""):
        request = f'GET /{resource} HTTP/1.1\r\nHost: {self.host}\r\n\r\n' # Construct request byte string.
        print(f"[RETRIEVING] GET /{resource} HTTP/1.1")
        self.encodeAndSend(request) # Send request to server.
        response = self.rvcChunks() # Read the server reply & store it in 'response'.
        contentType = self.findContentType(response)
        if contentType == b'text':
            charset = self.findCharset(response)
            self.bodyToString(response, resource ,charset) # Pass the byte response to bodyToString
            images = self.scrapeImages(resource)
            if images:
                print(f"[IMAGES FOUND] {images [0:2]}...")
                self.getImages(images)
            self.alterImageSrc(resource)
        elif contentType == b'image':
            self.writeImage(resource, response)
    

    """
    Retrieves the HEAD response from a certain webserver and stores the results locally.
    """
    def head(self):
        request = f'HEAD / HTTP/1.1\r\nHost: {self.host}\r\nConnection: close\r\n\r\n'
        print(f"[RETRIEVING] HEAD / HTTP/1.1")
        self.encodeAndSend(request)
        response = self.s.recv(1024)
        charset = self.findCharset(response)
        try:
            decodedResponse = response.decode(charset)
            self.writeFile(decodedResponse, "headers.txt")
        except LookupError:
            decodedResponse = response.decode('utf-8', errors='ignore')
            self.writeFile(decodedResponse, "headers.txt")


    def post(self, resource, body):
        contenLength = len(body)
        request = f'POST /{resource} HTTP/1.1\r\nHost: {self.host}\r\nContent-Length: {contenLength}\r\nConnection: close\r\n\r\n{body}\r\n\r\n'
        print(f"[SENDING] POST /{resource} HTTP/1.1")
        self.encodeAndSend(request)
        response = self.s.recv(2048)
        print(f"[CREATED] {response.decode()}")


    def put(self, resource, body):
        contenLength = len(body)
        request = f'PUT /{resource} HTTP/1.1\r\nHost: {self.host}\r\nContent-Length: {contenLength}\r\nConnection: close\r\n\r\n{body}\r\n\r\n'
        print(f"[SENDING] PUT /{resource} HTTP/1.1")
        self.encodeAndSend(request)
        response = self.s.recv(1024)
        print(f"[CREATED] {response.decode()}")


    """
    Retrieves all the chunks from a certain webpage and stores them.

    @return: The request response.
    """
    def rvcChunks(self):
        BUFFERSIZE = 4096
        response = b''
        totalLength = 0
        CRLFCounter = 0
        contentLength = sys.maxsize
        while True:
            data = self.s.recv(BUFFERSIZE)
            totalLength += len(data)      
            response += data

            if data.find(b"Content-Length:") != -1:
                startPos = data.find(b"Content-Length") # Start position in byte stream where "Content-Length" is found.
                findData = data[startPos:] # Returns the data from the start position in byte stream.
                endPos = findData.find(b"\r\n") # Finds the first occurence of "\r\n" in the byte stream after content length and save its position.
                contentLength = findData[16:endPos].decode() # Gets the content length bytes and decodes it to discover the total content contentLength of HTTP request.

            if data.find(b"\r\n\r\n") != -1:
                CRLFCounter += 1 

            if CRLFCounter >= 2 or totalLength >= int(contentLength): 
                # If second EOL/CRLF (line break) is found, break. (chunked encoding ends with a CRLF because of the terminating chunk with length zero)
                # If total received bytes from buffer exceeds or equals (should exceed because of additional bytes fomre the header ietself) actual content length -> break (content-lentgh).
                break
        return response


    """
    Looks for the charset in the response, more specifically in the HTTP header.

    @param response: The encoded response from the server.
    @return: The Content-Type charset to decode the response with.
    """
    def findCharset(self, response):
        charset = ""
        if response.find(b"Content-Type:"):
            headerEnd = response.find(b"\r\n\r\n") 
            range = response[:headerEnd]
            if range.find(b"charset="):
                startPos = range.find(b"charset=")
                findData = response[startPos:]
                endPos = findData.find(b"\r\n")
                charset = findData[8:endPos].decode()
            else:
                charset = 'utf-8'
        return charset


    """
    Looks for the content type in the response, more specifically in the HTTP header.

    @param response: The encoded response from the server.
    @return: The Content-Type to classify the response.
    """
    def findContentType(self, response):
        type = ""
        contentType = response.find(b"Content-Type:")
        newData = response[contentType:]
        start = newData.find(b" ")
        end = newData.find(b"\r\n")
        data = newData[start:end] 
        if data.find(b"/"):
            startPos = data.find(b" ")
            endPos = data.find(b"/")
            type = data[startPos + 1:endPos]
        return type


    """
    Creates the file that contains the requested content from a webpage. 

    @param html: The HTML that will be stored in the file.
    @param filename: Name of the file where the requested content is located.
    """
    def writeFile(self, content, filename):
        if filename == "":
            filename = "index.html"
        myDir = os.getcwd() + "/" + self.host
        if not os.path.exists(myDir):
            os.mkdir(myDir) # Create host folder.
        with open(myDir + "/" + filename, "w") as f: # Write file.
            f.write(content)


    """
    Removes the HTTP header from the response and converts decodes the byte stream. 

    @param response: The byte response from the HTTP request.
    """
    def bodyToString(self, response, resource, charset):
        endHeader = response.find(b'\r\n\r\n') # Remove HTTP header from response.
        bodyBytes = response[endHeader+4:]
        try:
            bodyString = bodyBytes.decode(charset) # Decode response to UTF-8.
            self.writeFile(bodyString, resource)
        except LookupError:
            bodyString = bodyBytes.decode('utf-8', errors='ignore') # Decode response to UTF-8.
            self.writeFile(bodyString, resource)  


    """
    Looks for all embedded images in the HTML body. 

    @return: A dictionary containing the src of all the images.
    """
    def scrapeImages(self, resource):
        if resource == "":
            resource = "index.html"
        images = []
        text_file = open(self.host + "/" + resource, "r")
        soup = bs.BeautifulSoup(text_file,'lxml')
        text_file.close()
        for image in soup.find_all('img'):
            images.append(image.get('src'))
        return images


    """
    Retrieves each image individually from a webpage. 

    @param images: Dictionary of all the images names to be retrieved from the webpage.
    """
    def getImages(self, images):
        for image in images:
            request = f'GET /{image} HTTP/1.1\r\nHost: {self.host}\r\n\r\n' # Construct request byte string.
            print(f"[RETRIEVING] GET /{image} HTTP/1.1")
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
        image = response.split(b'\r\n\r\n')[1] # Gets the image data and makes sure the header is excluded.
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
    def alterImageSrc(self, resource):
        if resource == "":
            resource = "index.html"
        body = open(os.getcwd() + "/" + self.host + "/" + resource, "r")
        soup = bs.BeautifulSoup(body, 'lxml')
        images = soup.find_all("img")
        for image in images:
            src = image.get('src')
            if src[0] == '/':
                image['src'] = src[1:]
        with open(os.getcwd() + "/" + self.host + "/" + resource, "w") as f:
             f.write(str(soup))