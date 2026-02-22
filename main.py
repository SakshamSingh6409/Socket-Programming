import socket
import json

user_details = {}  # Global variable to store authenticated user details

def process_commands(x, c):
    if x == "add_D_Cred":
        # existing employee input flow
        First_Name = input("Enter First Name: ")
        Last_Name = input("Enter Last Name: ")
        Branch = input("Branch of Employee: ")
        Role = input("Enter Role of Employee: ")
        Username = input("Username: ")
        Password = input("Password: ")
        Status = input("What is the status: ")

        employee_data = {
            "First_Name": First_Name,
            "Last_Name": Last_Name,
            "Branch": Branch,
            "Role": Role,
            "Username": Username,
            "Password": Password,
            "Status": Status
        }
        result = write_D_Cred(c, employee_data)
        print(result)

    elif x == "insert_row":
        table = input("Enter table name: ")
        data = json.loads(input("Enter row data as JSON: "))
        result = insert_row_client(c, table, data)
        print(result)

    elif x == "update_cell":
        table = input("Enter table name: ")
        target_column = input("Column to update: ")
        new_value = input("New value: ")
        conditions = json.loads(input("Enter conditions as JSON: "))
        result = update_cell_client(c, table, target_column, new_value, conditions)
        print(result)

    elif x == "get_table":
        table = input("Enter table name: ")
        result = get_table_client(c, table)
        print(result)

    elif x == "Disconnect":
        result = disconnect_client(c)
        print(result)
        return False

    return True

def recv_json(c):
    """Receive length-prefixed JSON."""
    raw_len = b''
    while len(raw_len) < 4:
        chunk = c.recv(4 - len(raw_len))
        if not chunk:
            raise ConnectionError("Socket closed")
        raw_len += chunk
    msg_len = int.from_bytes(raw_len, 'big')
    data = b''
    while len(data) < msg_len:
        chunk = c.recv(min(4096, msg_len - len(data)))
        if not chunk:
            raise ConnectionError("Socket closed")
        data += chunk
    return json.loads(data.decode())

def send_json(c, data):
    """Send JSON with length prefix."""
    msg = json.dumps(data).encode()
    length = len(msg).to_bytes(4, 'big')
    c.send(length + msg)

def insert_row_client(c, table, data):
    c.send("insert_row".encode())
    payload = {"table": table, "data": data}
    send_json(c, payload)
    resp = recv_json(c)
    if "success" in resp:
        return f"Row inserted into {table} with ID {resp['row_id']}"
    else:
        return f"Error: {resp['error']}"

def update_cell_client(c, table, target_column, new_value, conditions):
    c.send("update_cell".encode())
    payload = {
        "table": table,
        "target_column": target_column,
        "new_value": new_value,
        "conditions": conditions
    }
    send_json(c, payload)
    resp = recv_json(c)
    if "success" in resp:
        return f"Updated {table}: set {target_column} = {new_value} where {conditions}"
    else:
        return f"Error: {resp['error']}"

def get_table_client(c, table):
    c.send("get_table".encode())
    payload = {"table": table}
    send_json(c, payload)
    resp = recv_json(c)
    if "success" in resp:
        return resp
        ''' 
            for idx, row in resp["data"].items():
            print(f"{idx}: {row}")
        '''
    else:
        return(f"Error: {resp['error']}")

def disconnect_client(c):
    c.send("Disconnect".encode())
    return "Disconnected from server."

def write_D_Cred(c, employee_data):
    c.send("add_D_Cred".encode())
    send_json(c, employee_data)
    # Optionally wait for server confirmation
    response = recv_json(c)
    
    if "success" in response:
        return f"Employee added with ID {response['Employee_ID']}"
    else:
        return f"Error: {response['error']}"

def main():
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.connect(("100.86.253.5", 12345))

    mess = c.recv(1024).decode()

    if mess == "y":
        usr = input("Enter your username: ")
        pas = input("Enter your password: ")
        auth = {"username": usr, "password": pas}
        send_json(c, auth)
        try:
            mess2 = recv_json(c)
        except json.JSONDecodeError:
            print(f"Invalid JSON from server: {mess2}")
            return

        if mess2["response"] == "True":
            run = True
            global user_details
            user_details = mess2["Client_Detail"]
        else:
            print("Rejected by Server")
            run = False
    else:
        run = False

    while run:
        x = input("Enter anything [Type 'Disconnect' to exit]: ")
        if not process_commands(x, c):
            break

    c.close()
    print("Client stopped.")


if __name__ == "__main__":
    main()
