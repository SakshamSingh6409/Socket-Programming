import sqlite3

# Example dictionary with user data
user_data = {
    "Employee_ID": 2,
    "First_Name": "Saksham",
    "Last_Name": "Singh",
    "Branch": "admin",
    "Role": "admin",
    "Username": "saksham",
    "Password": "123",
    "Status": "Active"
}

# Connect to the database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Build the SQL dynamically from dictionary keys
columns = ", ".join(user_data.keys())
placeholders = ", ".join(["?"] * len(user_data))
sql = f"INSERT INTO Credentials ({columns}) VALUES ({placeholders})"

# Execute with values from the dictionary
cursor.execute(sql, tuple(user_data.values()))

# Commit and close
conn.commit()
conn.close()
