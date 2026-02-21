import socket
import json
import threading
from datetime import datetime
import sqlite3

# Track connected clients
clients = {}
client_counter = 0
lock = threading.Lock()    # to safely update shared data
db_file = "database1.db"
