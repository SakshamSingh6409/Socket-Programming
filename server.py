import socket
import json

valid_users = ["saksham"]

def user_H(c, addr):
    print("Connected to:", addr)
    c.send('y'.encode())

    auth = json.loads(c.recv(1024).decode())
    
    print("Authentication Received")

    if auth["username"] in valid_users:
        c.send(json.dumps(True).encode())
        while True:
            mess = c.recv(1024).decode()
            print("Received: ", mess)

            if mess == "0":
                global run
                run = False
                break
    else:
        print("Invalid User")
        c.send(json.dumps(False).encode())

    c.close()


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("100.86.253.5", 12345))
    s.listen(5)

    print("Server listening...")

    run = True
    while run:
        c, addr = s.accept()
        user_H(c, addr)

    s.close()
    print("Server stopped.")


if __name__ == "__main__":
    main()
