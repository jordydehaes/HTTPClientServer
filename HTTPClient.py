import socket
import sys
import os
import bs4 as bs
import time
import PIL.Image as Image

class HTTPClient:

    def __init__(self, host, port):
        self.host = host # The server's hostname.
        self.port = port # The port used to reach the host.
        self.s = self.createSocket() # Instantiate the socket and connect with host/port.


    def createSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create an IPv4, TCP socket.
        print(f"[SOCKET CREATED] {s}")
        s.connect((socket.gethostbyname(self.host), self.port)) # Connect to the host using the host name and port number.
        print(f"[SOCKET CONNECTED] {self.host} {self.port}")
        return s


    def encodeAndSend(self, data):
        bytes = data.encode('ascii') # Encode string to bytes.
        try:
            self.s.send(bytes) # Send the request to the server.
        except error:
            print(f"Error sending: {error}.")
            

    def executeRequest(self, host, requestType):
        self.host = host # Set the host.
        if requestType == 'GET': 
            self.get()
        elif requestType == 'POST':
            self.get()
        elif requestType == 'PUT':
            request = (f'PUT / HTTP/1.1\r\nHost: {host}\r\n\r\n')
        elif requestType == 'HEAD':
            self.head()
        else:
            print('Unknown request type')
            
        
    def get(self):
        request = f'GET / HTTP/1.1\r\nHost: {self.host}\r\n\r\n' # Construct request byte string.
        print(f"[RETRIEVING HTML] GET / HTTP/1.1")
        self.encodeAndSend(request) # Send request to server.
        response = self.rvcChunks() # Read the server reply & store it in 'response'.
        self.bodyToString(response) # Pass the byte response to bodyToString
        images = self.search_images()
        if images:
            print(f"[IMAGES FOUND] {images [0:2]}...")
            self.get_images(images)
        self.alterImageSrc()
    

    def head(self):
        request = f'HEAD / HTTP/1.1\r\nHost: {self.host}\r\n\r\n'
        self.encodeAndSend(request)
        response = self.rvcChunks()
        headers = open("headersHEAD.txt", "w")
        headers.write(response.decode("utf-8"))
        headers.close()


    def rvcChunks(self):
        response = b""
        totallength = 0
        emptylines = 0
        length = sys.maxsize

        while True:
            data = self.s.recv(4096)
            totallength += len(data)

            if data.find(b"Content-Length:") != -1:
                startpos = data.find(b"Content-Length")
                finddata = data[startpos:]
                endpos = finddata.find(b"\r\n")
                length = finddata[16:endpos].decode()

            if data.find(b"\r\n\r\n") != -1:
                emptylines += 1

            response += data

            if emptylines >= 2 or totallength >= int(length):
                break

        end = response.find(b"\r\n\r\n")
        header = response[:end]
        return response
        # socket.setblocking(0) # Set the socket to non-blocking.
        # total_data = [];
        # chunk = '';
        # begin = time.time() # Start the timer.
        # while 1:
        #     if total_data and time.time() - begin > timeout: # If there is data, break afgter timeout.
        #         break
        #     elif time.time()-begin > timeout*2: # If there is no data, wait a little longer.
        #         break
            
        #     try:
        #         chunk = socket.recv(10000)
        #         if chunk:
        #             total_data.append(chunk)
        #             begin = time.time() # Reset timer.
        #         else:
        #             time.sleep(0.1)
        #     except:
        #         pass
        # return b''.join(total_data) # Join all chunks together and return all the bytes.


    def writeBody(self, body):
        myDir = os.getcwd() + "/" + self.host
        if not os.path.exists(myDir):
            os.mkdir(myDir) 
        myFile = open(myDir + "/" + "index.html", "w") # Create host folder & write body.
        myFile.write(body)
        myFile.close()


    def bodyToString(self, response):
        bodyBytes = response.split(b'\r\n\r\n')[1] # Remove HTTP header from response.
        bodyString = bodyBytes.decode('utf-8', errors='ignore') # Decode response to UTF-8.
        self.writeBody(bodyString)


    def search_images(self):
        images = []
        text_file = open(self.host + "/" +"index.html", "r")
        soup = bs.BeautifulSoup(text_file,'lxml')
        text_file.close()
        for image in soup.find_all('img'):
            images.append(image.get('src'))
        return images


    def get_images(self, images):
        for image in images:
            request = f'GET /{image} HTTP/1.1\r\nHost: {self.host}\r\n\r\n' # Construct request byte string.
            print(f"[RETRIEVING IMAGE] GET /{image} HTTP/1.1")
            self.encodeAndSend(request) # Send request to server.
            response = self.rvcChunks() # Read the server reply & store it in 'response'.
            self.handle_get_image(image, response) # Pass the byte response to bodyToString

    
    def handle_get_image(self, image_name, response):
        image = response.split(b'\r\n\r\n')[1]
        if image_name.startswith('/'):
            image_name = image_name[1:]
        if image_name.find('/'):
            os.makedirs(os.getcwd() + "/" + self.host + "/" + os.path.dirname(image_name), exist_ok=True)
            with open(os.getcwd() + "/" + self.host + "/" + image_name, "wb") as f:
                f.write(image)
        else:
            with open(os.getcwd() + "/" + self.host + "/" + image_name, "wb") as f:
                f.write(image)


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



#httpClient = HTTPClient("www.linux-ip.net", 80)
#httpClient = HTTPClient("www.tinyos.net", 80)
#httpClient = HTTPClient("www.google.com", 80)
#httpClient.get()
#httpClient.head()