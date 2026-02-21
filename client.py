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
        write_D_Cred(c, employee_data)

    elif x == "insert_row":
        table = input("Enter table name: ")
        data = json.loads(input("Enter row data as JSON: "))
        insert_row_client(c, table, data)

    elif x == "update_cell":
        table = input("Enter table name: ")
        target_column = input("Column to update: ")
        new_value = input("New value: ")
        conditions = json.loads(input("Enter conditions as JSON: "))
        update_cell_client(c, table, target_column, new_value, conditions)

    elif x == "get_table":
        table = input("Enter table name: ")
        get_table_client(c, table)

    elif x == "Disconnect":
        disconnect_client(c)
        return False

    return True


def insert_row_client(c, table, data):
    payload = {"table": table, "data": data}
    c.send("insert_row".encode())
    c.send(json.dumps(payload).encode())
    resp = json.loads(c.recv(4096).decode())
    if "success" in resp:
        print(f"Row inserted into {table} with ID {resp['row_id']}")
    else:
        print(f"Error: {resp['error']}")

def update_cell_client(c, table, target_column, new_value, conditions):
    payload = {
        "table": table,
        "target_column": target_column,
        "new_value": new_value,
        "conditions": conditions
    }
    c.send("update_cell".encode())
    c.send(json.dumps(payload).encode())
    resp = json.loads(c.recv(4096).decode())
    if "success" in resp:
        print(f"Updated {table}: set {target_column} = {new_value} where {conditions}")
    else:
        print(f"Error: {resp['error']}")

def get_table_client(c, table):
    payload = {"table": table}
    #c.send("get_table".encode())
    c.send(json.dumps(payload).encode())
    resp = json.loads(c.recv(8192).decode())
    if "success" in resp:
        print(f"Data from {table}:")
        for idx, row in resp["data"].items():
            print(f"{idx}: {row}")
    else:
        print(f"Error: {resp['error']}")

def disconnect_client(c):
    c.send("Disconnect".encode())
    print("Disconnected from server.")

def write_D_Cred(c, employee_data):
    c.send(json.dumps(employee_data).encode())
    # Optionally wait for server confirmation
    response = c.recv(1024).decode()
    resp = json.loads(response)
    
    if "success" in resp:
        print(f"Employee added with ID {resp['Employee_ID']}")
    else:
        print(f"Error: {resp['error']}")

def main():
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.connect(("100.86.253.5", 12345))

    mess = c.recv(1024).decode()

    if mess == "y":
        usr = input("Enter your username: ")
        pas = input("Enter your password: ")
        auth = {"username": usr, "password": pas}
        c.send(json.dumps(auth).encode())
        raw = c.recv(1024).decode()
        if not raw:
            print("No response from server.")
            return
        try:
            mess2 = json.loads(raw)
        except json.JSONDecodeError:
            print(f"Invalid JSON from server: {raw}")
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
        c.send(x.encode())
        if not process_commands(x, c):
            break
    

    c.close()
    print("Client stopped.")


if __name__ == "__main__":
    main()
