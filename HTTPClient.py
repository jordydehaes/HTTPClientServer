import socket
import sys
import os
import bs4 as bs
import time
import PIL.Image as Image

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create an IPv4, TCP socket.

class HTTPClient:

    def __init__(self, host, port):
        self.host = host # The server's hostname.
        self.port = port # The port used to reach the host.
        s.connect((socket.gethostbyname(host), self.port)) # Connect to the host using the host name and port number.

    def get_html(self):
        request = bytes(f'GET / HTTP/1.1\r\nHost: {self.host}\r\n\r\n','utf-8') # Construct request byte string.
        s.sendall(request) # Send request to server.
        response = self.recv_bytes_timer(s) # Read the server reply & store it in 'response'.
        self.handle_get_response(response) # Pass the byte response to handle_get_response
        images = self.search_images()
        if images:
            self.get_images(images)
        print(f'Succesfully processed GET on {self.host}!')
    
    def head(self):
        request = bytes(f'HEAD / HTTP/1.1\r\nHost: {self.host}\r\n\r\n','utf-8')
        s.sendall(request)
        response = self.recv_bytes_timer(s)
        text_file = open("headersHEAD.txt", "w")
        n = text_file.write(response.decode("utf-8", errors="ignore"))
        text_file.close()
        print(f'Succesfully processed HEAD on {self.host}!')

    def recv_bytes_timer(self, socket, timeout=2):
        socket.setblocking(0) # Set the socket to non-blocking.
        total_data = [];
        chunk = '';
        begin = time.time() # Start the timer.
        while 1:
            if total_data and time.time() - begin > timeout: # If there is data, break afgter timeout.
                break
            elif time.time()-begin > timeout*2: # If there is no data, wait a little longer.
                break
            
            try:
                chunk = socket.recv(10000)
                if chunk:
                    total_data.append(chunk)
                    begin = time.time() # Reset timer.
                else:
                    time.sleep(0.1)
            except:
                pass
        return b''.join(total_data) # Join all chunks together and return all the bytes.

    def handle_get_response(self, response):
        text_file1 = open("index.html", "w")
        n1 = text_file1.write(response.decode("utf-8", errors="ignore"))
        text_file1.close()

        text_file2 = open("index.html", "r")
        soup = bs.BeautifulSoup(text_file2,'lxml')
        text_file2.close()
        extract_headers = soup.find('html').find('p').extract().get_text()
        
        html = soup.find('html').prettify() 
        text_file4 = open("index.html", "w")
        n3 = text_file4.write(str(html))
        text_file4.close()

    def search_images(self):
        images = []
        text_file = open("index.html", "r")
        soup = bs.BeautifulSoup(text_file,'lxml')
        text_file.close()
        for image in soup.find_all('img'):
            images.append(image.get('src'))
        return images

    def get_images(self, images):
        for image in images:
            request = bytes(f'GET /{image} HTTP/1.1\r\nHost: {self.host}\r\n\r\n','utf-8') # Construct request byte string.
            s.sendall(request) # Send request to server.
            response = self.recv_bytes_timer(s) # Read the server reply & store it in 'response'.
            self.handle_get_image(image, response) # Pass the byte response to handle_get_response
        print(f'Succesfully processed GET Images on {self.host}!')

    def handle_get_image(self, image_name, response):
        image = response.split(b'\r\n\r\n')[1]
        if image_name.startswith('/'):
            os.makedirs(os.getcwd() + os.path.dirname(image_name), exist_ok=True)
            with open(os.getcwd() + image_name, "wb") as f:
                f.write(image)
        else:
            with open(image_name, "wb") as f:
                f.write(image)

httpClient = HTTPClient("www.linux-ip.net", 80)
#httpClient = HTTPClient("www.tinyos.net", 80)
#httpClient = HTTPClient("www.tcpipguide.com", 80)
httpClient.get_html()

s.close()