import socket
import json
import threading
from datetime import datetime
import sqlite3
import bcrypt

from server_variables import *

def process_command(x, c, client_id, username, errors, timestamp):
    try:
        if x == "add_D_Cred":
            write_D_Cred(c, db_file, clients[client_id]["clearance"], clients[client_id]["branch"])
        
        elif x == "insert_row":
            payload = json.loads(c.recv(4096).decode())
            table = payload["table"]
            data = payload["data"]

            role = clients[client_id]["clearance"]
            branch = clients[client_id]["branch"]

            try:
                new_id = insert_row(db_file, table, data, role, branch)
                c.send(json.dumps({"success": True, "row_id": new_id}).encode())
            except Exception as e:
             c.send(json.dumps({"error": str(e)}).encode())


        elif x == "update_cell":
            # Client sends: {"table": "Credentials", "target_column": "Status",
            #                "new_value": "Inactive", "conditions": {"Username": "abc"}}
            payload = json.loads(c.recv(4096).decode())
            update_cell(db_file,
                        payload["table"],
                        payload["target_column"],
                        payload["new_value"],
                        payload["conditions"])
            c.send(json.dumps({"success": True}).encode())

        elif x == "get_table":
            # Client sends: {"table": "Credentials"}
            payload = json.loads(c.recv(4096).decode())
            table = payload["table"]
            data = table_to_nested_dict(db_file, table)
            c.send(json.dumps({"success": True, "data": data}).encode())

        elif x == "Disconnect":
            return True  # Signal to disconnect

        else:
            print(f"[{client_id} | {username}] Unknown command: {x}")

    except Exception as e:
        errors[timestamp] = str(e)
        c.send(json.dumps({"error": str(e)}).encode())

def has_permission(db_file, role, branch, table, action):
    """
    Check if a user has permission for a given action on a table.
    action: "view", "insert", "update", "delete"
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT Editor, Viewer, Tables FROM Roles WHERE Role=? AND Branch=?", (role, branch))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    editor, viewer, tables_str = row
    try:
        tables = json.loads(tables_str)
    except Exception:
        tables = [t.strip() for t in tables_str.strip("[]").split(",")]

    # Admin case: if "All tables" is in list
    if "All tables" in tables:
        return True

    # Check table access
    if table not in tables:
        return False
    # Check action permissions
    if action == "view" and viewer == 1:
        return True
    if action in ("insert", "update", "delete") and editor == 1:
        return True

    return False

def write_D_Cred(c, db_file, role, branch):
    """Insert new employee credentials into database using insert_row()."""
    
    if not has_permission(db_file, role, branch, "Credentials", "insert"):
        raise PermissionError(f"{role} not allowed to insert into Credentials")
    try:
        user_data = json.loads(c.recv(1024).decode())
        print("Received user_data:", user_data)  # debug
    except Exception as e:
        print(f"Error receiving user data: {e}")
        c.send(json.dumps({"error": "Invalid data"}).encode())
        return

    # Hash the password before storing
    user_data["Password"] = bcrypt.hashpw(
        user_data["Password"].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    try:
        # Use insert_row() instead of hardcoded SQL
        new_id = insert_row(db_file, "Credentials", user_data)
        c.send(json.dumps({"success": True, "Employee_ID": new_id}).encode())
        print(f"Inserted row with Employee_ID {new_id}")
    except Exception as e:
        print(f"Error inserting data: {e}")
        c.send(json.dumps({"error": str(e)}).encode())

def log(client_info, commands, errors, db_file):
    """Insert a log entry into Logs table."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Prepare values
    user = client_info["username"] or "unknown"
    ip = client_info["addr"][0]
    clearance = client_info["clearance"] or "none"
    login_time = client_info["login_time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] #Gives time in according to UTC Time
    duration = str(datetime.now() - client_info["login_time"])

    # Convert dicts to JSON for storage
    commands_json = json.dumps(commands, indent=2)
    errors_json = json.dumps(errors, indent=2)

    sql = """INSERT INTO Logs 
             (User, IP, Clearance, Login_time, Logout_time, Duration, Commands, Errors)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

    cursor.execute(sql, (user, ip, clearance, login_time, logout_time,
                         duration, commands_json, errors_json))
    conn.commit()
    conn.close()

def update_cell(db_file, table, target_column, new_value, conditions, role, branch):
    """
    Update a single cell in an SQLite database.

    Args:
        db_file (str): Path to the .db file
        table (str): Table name
        target_column (str): Column to update
        new_value (any): New value to set in target_column
        conditions (dict): Dictionary of {column: value} to filter rows
    """

    if not has_permission(db_file, role, branch, table, "update"):
        raise PermissionError(f"{role} not allowed to update {table}")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Build WHERE clause dynamically from conditions
    where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
    sql = f"UPDATE {table} SET {target_column} = ? WHERE {where_clause}"

    params = [new_value] + list(conditions.values())
    cursor.execute(sql, params)

    conn.commit()
    conn.close()
    print(f"Updated {target_column} to {new_value} where {conditions}")

def insert_row(db_file, table, data_dict, role, branch):
    """
    Insert a row into any table using a dictionary of column-value pairs.
    Only fills the columns provided in data_dict.

    Returns:
        int: The auto-generated row ID (e.g., Employee_ID if it's INTEGER PRIMARY KEY AUTOINCREMENT)
    """
    if not has_permission(db_file, role, branch, table, "insert"):
        raise PermissionError(f"{role} not allowed to insert into {table}")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Get table column names
    cursor.execute(f"PRAGMA table_info({table})")
    columns_info = cursor.fetchall()
    table_columns = [col[1] for col in columns_info]

    # Ensure keys match actual table columns
    for key in data_dict.keys():
        if key not in table_columns:
            conn.close()
            raise ValueError(f"Invalid column name: {key}")

    # Build query dynamically
    columns = ", ".join(data_dict.keys())
    placeholders = ", ".join(["?" for _ in data_dict])
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    cursor.execute(sql, list(data_dict.values()))
    conn.commit()

    # Capture the auto-generated primary key
    new_id = cursor.lastrowid

    conn.close()
    print(f"Inserted row into {table}: {data_dict} (ID={new_id})")
    return new_id

def table_to_nested_dict(db_file, table, role, branch):
    """
    Convert a table into a nested dictionary:
    { row_index: {column1: value1, column2: value2, ...}, ... }

    Args:
        db_file (str): Path to the .db file
        table (str): Table name
    """
    if not has_permission(db_file, role, branch, table, "view"):
        raise PermissionError(f"{role} not allowed to view {table}")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    nested_dict = {}
    for idx, row in enumerate(rows, start=1):  # row_index starts at 1
        row_dict = dict(zip(column_names, row))
        nested_dict[idx] = row_dict

    conn.close()
    return nested_dict

def verify_credentials(db_file, client_info):
    """Verify if username and password are valid."""
    
    data = table_to_nested_dict(db_file, "Credentials", "Admin", "Admin")  # Use admin role to read credentials

    for row in data.values():
        if row["Username"] == client_info["username"]:
            stored_hash = row["Password"]
            if bcrypt.checkpw(client_info["password"].encode('utf-8'), stored_hash.encode('utf-8')):
                client_info["role"] = row["Role"]
                return True
            else:
                return False
    return False

def handle_C(c, addr):
    """Handle a single client connection."""
    global client_counter
    commands = {}
    errors = {}

    with lock:
        client_counter += 1
        client_id = f"c{client_counter}"
        clients[client_id] = {
            "id": client_id,
            "socket": c,
            "addr": addr,
            "username": None,
            "password": None,
            "clearance": None,
            "login_time": datetime.now()
        }

    print(clients)
    print(f"{client_id} connected from {addr}")
    c.send('y'.encode())
    

    try:
        auth = json.loads(c.recv(1024).decode())
        username = auth.get("username")
        password = auth.get("password")

        clients[client_id]["username"] = username
        clients[client_id]["password"] = password

        client_copy = clients[client_id].copy()
        client_copy.pop("socket", None)  # remove "socket" before sending to client

        if verify_credentials(db_file, clients[client_id]):
            c.send(json.dumps({"response": "True", "Client_Detail": client_copy}).encode())
            while True:
                mess = c.recv(1024).decode()
                if not mess:
                    break

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                commands[timestamp] = mess

                if process_command(mess, c, client_id, username, errors, timestamp):
                    break
        else:
            c.send(json.dumps({"response": "False", "Client_Detail": client_copy}).encode())

    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        errors[timestamp] = str(e)

    finally:
        log(clients[client_id], str(commands), str(errors), db_file)  # <-- call logging here
        c.close()
        with lock:
            del clients[client_id]
        print(f"{client_id} disconnected")