import sqlite3
from collections import defaultdict

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT Branch, Role, Employee_ID, First_Name, Last_Name, Username
    FROM Credentials
    WHERE Status = 'Active'
    ORDER BY Branch, Role;
""")

rows = cursor.fetchall()

# Build nested dictionary: {Branch: {Role: [employees...]}}
data = defaultdict(lambda: defaultdict(list))

for branch, role, emp_id, fname, lname, uname in rows:
    data[branch][role].append({
        "Employee_ID": emp_id,
        "First_Name": fname,
        "Last_Name": lname,
        "Username": uname
    })

print(data)
