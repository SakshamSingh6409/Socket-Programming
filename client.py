import socket

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(("localhost", 12345))

mess = c.recv(1024).decode()

if mess == "y":
    run = True
else:
    run = False

while run:
    x = input("Enter anything [0 to exit]: ")
    c.send(x.encode())
    if x == "0":
        run = False

c.close()
print("Client stopped.")
