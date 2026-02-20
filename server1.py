import socket
import json
import threading
from datetime import datetime
import sqlite3

# Valid users and their clearance levels
valid_users = {
    "saksham": "admin",
    "guest": "low"
}

# Track connected clients
clients = {}
client_counter = 0
lock = threading.Lock()  # to safely update shared data


def get_D():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Credentials")
    rows = cursor.fetchall()

    column_name = [description[0] for description in cursor.description]
    print(column_name)
    for row in rows:
        print(row)

    conn.close()


def add_D(c):
    res = c.recv(1024).decode()
    if res == "0":
        write_D_Cred(c)
    elif res == "1":
        write_D_Comp(c)


def write_D_Comp(c):
    # Placeholder for company database logic
    pass


def write_D_Cred(c):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        user_data = json.loads(c.recv(1024).decode())
    except Exception as e:
        print(f"Error receiving user data: {e}")
        c.send(json.dumps({"error": "Invalid data"}).encode())
        conn.close()
        return

    # Build SQL dynamically from dictionary keys
    columns = ", ".join(user_data.keys())
    placeholders = ", ".join(["?"] * len(user_data))
    sql = f"INSERT INTO Credentials ({columns}) VALUES ({placeholders})"

    try:
        cursor.execute(sql, tuple(user_data.values()))
        conn.commit()
        # Return the new auto-incremented Employee_ID
        new_id = cursor.lastrowid
        c.send(json.dumps({"success": True, "Employee_ID": new_id}).encode())
    except Exception as e:
        print(f"Error inserting data: {e}")
        c.send(json.dumps({"error": "Database insert failed"}).encode())
    finally:
        conn.close()


def handle_C(c, addr):
    global client_counter

    # Assign unique client ID
    with lock:
        client_counter += 1
        client_id = f"c{client_counter}"
        clients[client_id] = {
            "id": client_id,
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

        clients[client_id]["username"] = username
        clients[client_id]["clearance"] = valid_users.get(username, "none")

        print(f"Authentication received from {client_id} ({username})")

        if username in valid_users:
            c.send(json.dumps(True).encode())
            while True:
                mess = c.recv(1024).decode()
                if not mess:
                    break

                if mess == "add_D":
                    add_D(c)
                elif mess == "Disconnect":
                    print(f"{client_id} ({username}) requested disconnect")
                    break
                else:
                    print(f"[{client_id} | {username}] {mess}")
        else:
            print(f"{client_id} invalid user: {username}")
            c.send(json.dumps(False).encode())

    except Exception as e:
        print(f"Error with {client_id}: {e}")

    finally:
        logout_time = datetime.now()
        login_time = clients[client_id]["login_time"]
        duration = logout_time - login_time
        print(f"{clients[client_id]['id']} ({clients[client_id]['username']}) disconnected after {duration}")
        c.close()
        with lock:
            del clients[client_id]


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("100.86.253.5", 12345))
    s.listen(4000)

    print("Server listening...")

    try:
        while True:
            c, addr = s.accept()
            threading.Thread(target=handle_C, args=(c, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        s.close()


if __name__ == "__main__":
    main()
