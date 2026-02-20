import socket
import json



def add_D():
    print("which data do you want to add")
    print("\t\t\tEmployee Credentials [Enter 0]")
    print("\t\t\tCompany Database [Enter 1]")
    
    res = int(input("Your responce: "))
    if res == 0:
        write_D_Cred()

    if res == 1:
        wirte_D_Comp()



def write_D_Comp():
    pass


def write_D_Cred():
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

    c.send(json.dumps(employee_data).encode())

def main():
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
        elif x == "add_D":
            add_D()
        
    c.close()
    print("Client stopped.")


if __name__ = "__main__":
    main()
