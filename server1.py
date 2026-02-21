import socket
import threading

import server_functions as s_f

def main():
    """Start the server and accept clients."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("100.86.253.5", 12345))
    s.listen(4000)

    print("Server listening...")

    try:
        while True:
            c, addr = s.accept()
            threading.Thread(target=s_f.handle_C, args=(c, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        s.close()


if __name__ == "__main__":
    main()
