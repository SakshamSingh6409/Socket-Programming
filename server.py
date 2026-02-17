import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("100.86.253.5", 12345))
s.listen(5)

print("Server listening...")

run = True
while run:
    c, addr = s.accept()
    print("Connected to:", addr)
    c.send('y'.encode())

    while True:
        x = c.recv(1024).decode()
        if not x:
            break
        print("Received:", x)
        auth = json.loads(x)
        print("Username: ", auth["username"])
        print("password: ", auth["password"])
        if x == "0":
            run = False
            break

    c.close()

s.close()
print("Server stopped.")
