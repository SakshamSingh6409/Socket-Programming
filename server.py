import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("100.86.253.5", 12345))
s.listen(5)

print("Server listening...")

run = True
while run:
    c, addr = s.accept()
    print("Connected to:", addr)
    c.send('y'.encode())

    while True:
        auth = json.loads(c.recv(1024).decode())

        if not auth:
            break

        print("Authentication Received")

        if auth["username"] in username:
            c.send(json.dumps(True).encode())
            while True:
                mess = ercv(1024).decode()
                print("Received: ", mess)

                if mess == "0":
                    run = False
                    break

    c.close()

s.close()
print("Server stopped.")
