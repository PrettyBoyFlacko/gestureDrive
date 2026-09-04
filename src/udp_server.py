import socket

global UDP_IP
global UDP_PORT
global sock

def init(ip: str, port: int):
    global UDP_IP, UDP_PORT, sock
    UDP_IP = ip
    UDP_PORT = port 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(msg):
    sock.sendto(msg, (UDP_IP, UDP_PORT))