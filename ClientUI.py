from HTTPClient import HTTPClient


URI = input("Host: ")
port = input("Port: ")
client = HTTPClient(URI, port)

while True:
    httpCommand = input("HTTP Command: ")
    if httpCommand.lower() == "get":
        resource = input("Resource: ")
        client.executeRequest(URI, httpCommand, resource, body="")
    elif httpCommand.lower() == "put" or httpCommand.lower() == "post":
        resource = input("Resource: ")
        body = input("Body: ")
        client.executeRequest(URI, httpCommand, resource, body)
    else: 
        client.executeRequest(URI, httpCommand)