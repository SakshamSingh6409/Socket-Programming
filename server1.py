import socket
import json
import threading
from datetime import datetime

# Valid users and their clearance levels
valid_users = {
    "saksham": "admin",
    "guest": "low"
}

# Track connected clients
clients = {}
client_counter = 0
lock = threading.Lock()  # to safely update shared data

def handle_client(c, addr):
    global client_counter

    # Assign unique client ID
    with lock:
        client_counter += 1
        client_id = f"c{client_counter}"
        clients[client_id] = {
            "socket": c,
            "addr": addr,
            "username": None,
            "clearance": None,
            "login_time": datetime.now()
        }

    print(clients)

    print(f"{client_id} connected from {addr}")
    c.send('y'.encode())

    try:
        # Authentication
        auth = json.loads(c.recv(1024).decode())
        username = auth.get("username")
        password = auth.get("password")  # not used here, but you can validate

        clients[c]["username"client_id] = username
        clients[c]["clearance"] = valid_users.get(username, "none")

        print(f"Authentication received from {client_id} ({username})")

        if username in valid_users:
            c.send(json.dumps(True).encode())
            while True:
                mess = c.recv(1024).decode()
                if not mess:
                    break
                print(f"[{client_id} | {username}] {mess}")
                if mess == "0":
                    print(f"{client_id} ({username}) requested disconnect")
                    break
        else:
            print(f"{client_id} invalid user: {username}")
            c.send(json.dumps(False).encode())

    except Exception as e:
        print(f"Error with {client_id}: {e}")

    finally:
        logout_time = datetime.now()
        login_time = clients[]["login_time"]
        duration = logout_time - login_time
        print(f"{clients[c]['id']} ({clients[c]['username']}) disconnected after {duration}")
        c.close()
        with lock:
            del clients[c]

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("100.86.253.5", 12345))
    s.listen(5)

    print("Server listening...")

    try:
        while True:
            c, addr = s.accept()
            threading.Thread(target=handle_client, args=(c, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        s.close()

if __name__ == "__main__":
    main()
