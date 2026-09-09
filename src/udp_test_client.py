import socket

UDP_IP = input("Enter IP address. " \
"Use 'ip address' on Unix or 'ipconfig' on Windows to find IP addresses" \
"of this machine. Use 127.0.0.1 if the server is the same machine: ")
UDP_PORT = int(input("Enter port number: "))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)
    print("Received message: %s" % data)