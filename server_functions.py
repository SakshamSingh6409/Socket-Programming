import socket
import json
import threading
from datetime import datetime
import sqlite3

from server_variables import *
'''
def get_D():
    """Fetch and print all rows from Credentials table."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Credentials")
    rows = cursor.fetchall()
    column_name = [description[0] for description in cursor.description]
    print(column_name)
    for row in rows:
        print(row)
    conn.close()
'''

def add_D(c):
    """Handle adding data choice from client."""
    res = c.recv(1024).decode()  # receive choice: "0" or "1"
    if res == "0":
        write_D_Cred(c)
    elif res == "1":
        write_D_Comp(c)


def write_D_Comp(c):
    # Placeholder for company database logic
    pass


def write_D_Cred(c, db_file):
    """Insert new employee credentials into database."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        user_data = json.loads(c.recv(1024).decode())
        print("Received user_data:", user_data)  # debug
    except Exception as e:
        print(f"Error receiving user data: {e}")
        c.send(json.dumps({"error": "Invalid data"}).encode())
        conn.close()
        return

    sql = """INSERT INTO Credentials 
             (First_Name, Last_Name, Branch, Role, Username, Password, Status)
             VALUES (?, ?, ?, ?, ?, ?, ?)"""

    try:
        cursor.execute(sql, (
            user_data["First_Name"],
            user_data["Last_Name"],
            user_data["Branch"],
            user_data["Role"],
            user_data["Username"],
            user_data["Password"],
            user_data["Status"]
        ))
        conn.commit()
        new_id = cursor.lastrowid
        c.send(json.dumps({"success": True, "Employee_ID": new_id}).encode())
        print(f"Inserted row with Employee_ID {new_id}")
    except Exception as e:
        print(f"Error inserting data: {e}")
        c.send(json.dumps({"error": str(e)}).encode())
    finally:
        conn.close()


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


#Needs Testing and application
def update_cell(db_file, table, target_column, new_value, conditions):
    """
    Update a single cell in an SQLite database.

    Args:
        db_file (str): Path to the .db file
        table (str): Table name
        target_column (str): Column to update
        new_value (any): New value to set in target_column
        conditions (dict): Dictionary of {column: value} to filter rows
    """
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



#Needs Testing and application
def table_to_nested_dict(db_file, table):
    """
    Convert a table into a nested dictionary:
    { row_index: {column1: value1, column2: value2, ...}, ... }

    Args:
        db_file (str): Path to the .db file
        table (str): Table name
    """
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


def insert_row(db_file, table, data_dict):
    """
    Insert a row into any table using a dictionary of column-value pairs.
    Automatically checks that the number of keys matches the number of columns.

    Args:
        db_file (str): Path to the .db file
        table (str): Table name
        data_dict (dict): {column: value} pairs to insert

    Raises:
        ValueError: If number of keys in data_dict does not match table columns
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Get table column names
    cursor.execute(f"PRAGMA table_info({table})")
    columns_info = cursor.fetchall()
    table_columns = [col[1] for col in columns_info]  # col[1] is the column name

    # Check column count
    if len(data_dict.keys()) != len(table_columns):
        conn.close()
        raise ValueError(
            f"Column count mismatch: table has {len(table_columns)} columns, "
            f"but {len(data_dict.keys())} keys were provided."
        )

    # Ensure keys match actual table columns
    for key in data_dict.keys():
        if key not in table_columns:
            conn.close()
            raise ValueError(f"Invalid column name: {key}")

    # Build query
    columns = ", ".join(data_dict.keys())
    placeholders = ", ".join(["?" for _ in data_dict])
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    cursor.execute(sql, list(data_dict.values()))
    conn.commit()
    conn.close()
    print(f"Inserted row into {table}: {data_dict}")


def verify_credentials(db_file, table, username, password):
    """
    Verify if username and password are valid.
    """
    data = table_to_nested_dict(db_file, table)

    for row in data.values():
        if row["Username"] == username:
            stored_hash = row["Password"]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
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
        clients[client_id]["clearance"] = valid_users.get(username, "none")
    
        if username in valid_users:
            c.send(json.dumps(True).encode())
            while True:
                mess = c.recv(1024).decode()
                if not mess:
                    break

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                commands[timestamp] = mess

                if mess == "add_D":
                    try:
                        add_D(c)
                    except Exception as e:
                        errors[timestamp] = str(e)
                elif mess == "Disconnect":
                    break
                else:
                    print(f"[{client_id} | {username}] {mess}")
        else:
            c.send(json.dumps(False).encode())

    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        errors[timestamp] = str(e)

    finally:
        log(clients[client_id], str(commands), str(errors), db_file)  # <-- call logging here
        c.close()
        with lock:
            del clients[client_id]

