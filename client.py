import socket
import json

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(("100.86.253.5", 12345))

mess = c.recv(1024).decode()

if mess == "y":
    usr = input("Enter your username: ")
    pas = input("Enter your password: ")
    auth = {"username": usr, "password": pas}
    c.send(json.dumps(auth).encode())
    mess2 = json.loads(c.recv(1024).decode())
    if mess2 == True:
        run = True
    else:
        print("Rejected by Server")
        run = False
else:
    run = False

while run:
    x = input("Enter anything [0 to exit]: ")
    c.send(x.encode())
    if x == "0":
        run = False

c.close()
print("Client stopped.")
