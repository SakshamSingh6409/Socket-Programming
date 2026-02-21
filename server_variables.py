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
db_file = "database.db"
