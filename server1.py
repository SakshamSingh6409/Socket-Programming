import socket
import select

# Create server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("100.86.253.5", 12345))
s.listen(5)

print("Server listening...")

clients = []  # list to store client sockets
run = True

while run:
    # Monitor server socket + all client sockets
    readable, _, _ = select.select([s] + clients, [], [])

    for sock in readable:
        if sock is s:
            # New client connection
            c, addr = s.accept()
            print("Connected to:", addr)
            c.send('y'.encode())
            clients.append(c)
        else:
            # Existing client sent data
            data = sock.recv(1024).decode()
            if not data:
                # Client disconnected
                print("Client disconnected")
                clients.remove(sock)
                sock.close()
                continue

            print("Received:", data)

            if data == "0":
                run = False
                break

            # Broadcast to all clients
            for c in clients:
                if c is not sock:  # don’t echo back to sender
                    c.sendall(f"Broadcast: {data}".encode())

# Cleanup
for c in clients:
    c.close()
s.close()
print("Server stopped.")
