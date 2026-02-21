import sqlite3
import bcrypt

def hash_existing_passwords(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Fetch all rows
    cursor.execute("SELECT Employee_ID, Username, Password FROM Credentials")
    rows = cursor.fetchall()

    for emp_id, username, plain_pw in rows:
        # Skip if already looks like a bcrypt hash
        if plain_pw.startswith("$2a$") or plain_pw.startswith("$2b$") or plain_pw.startswith("$2y$"):
            print(f"Skipping {username} (already hashed)")
            continue

        # Hash the plain text password
        hashed_pw = bcrypt.hashpw(plain_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Update the row
        cursor.execute(
            "UPDATE Credentials SET Password = ? WHERE Employee_ID = ?",
            (hashed_pw, emp_id)
        )
        print(f"Updated {username}: {plain_pw} -> {hashed_pw}")

    conn.commit()
    conn.close()
    print("All plain text passwords have been hashed.")

if __name__ == "__main__":
    # Adjust path to your DB file
    hash_existing_passwords("database1.db")