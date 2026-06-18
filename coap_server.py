import socket

HOST = "0.0.0.0"
PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("UDP Server running on port", PORT)
print("Waiting for messages...\n")

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode()

    print("Device IP:", addr[0])
    print("Door Status:", message)
    print("----------------------")