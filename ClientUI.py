from HTTPClient import HTTPClient


httpCommand = input("HTTP Command:" )
URI = input("Host:" )
port = input("Port:" )

client = HTTPClient(URI, port)
client.executeRequest(URI, httpCommand)
