from socket import *
import socket
import threading
import time
from datetime import datetime

# ========= SERVER CLASS ==========
class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                data = self.connection.recv(32)
                if data:
                    data = data.decode('utf-8') #e. Data dalam bentuk UTF-8

                    #c. Request harus diawali "TIME" dan diakhiri \r\n (CR LF)
                    if data.startswith("TIME") and data.endswith("\r\n"):
                        # i. Respon diawali dengan "JAM<spasi>"
                        # ii. Format jam adalah "hh:mm:ss"
                        # iii. Respon diakhiri dengan \r\n
                        resp = "JAM " + datetime.strftime(datetime.now(), "%H:%M:%S") + "\r\n"
                        print(f"[SENDING] to {self.address}: {resp.strip()}")
                        self.connection.sendall(resp.encode('utf-8')) # Dikirim dalam UTF-8

                    # Permintaan dapat diakhiri dengan "QUIT\r\n"       
                    elif data.startswith("QUIT"):
                        print(f"[CLIENT EXIT] {self.address} disconnected.")
                        break
                    else:
                        print(f"[INVALID REQUEST] from {self.address}")
                        self.connection.sendall(b"Invalid request\r\n")
                        break
            except OSError:
                break
        self.connection.close()

# a. Membuka port 45000 dengan transport TCP
class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # a. Transport TCP
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 45000)) # a. Listening di port 45000
        self.my_socket.listen(5)
        print("[SERVER] Listening on port 45000...")
        while True:
            connection, client_address = self.my_socket.accept()
            print(f"[CONNECTION] from {client_address}")
            clt = ProcessTheClient(connection, client_address)  # b. Mulai thread untuk client
            clt.start()
            self.the_clients.append(clt)

# ========= CLIENT FUNCTION ==========
def run_client():
    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(('0.0.0.0', 45000))
        while True:
            req = input("Input your message (TIME / QUIT): ")
            if req == "QUIT":
                clientsocket.sendall(req.encode())
                print("QUITING...")
                clientsocket.close()
                print("Gracefully closed the connection.")
                break
            elif req.startswith("TIME"):
                clientsocket.sendall((req + "\r\n").encode())
                data = clientsocket.recv(1024)
                print("Response from server:", data.decode('utf-8').strip())
            else:
                print("Unknown command.")
    except Exception as e:
        print("Client error:", e)
    finally:
        clientsocket.close()

# ========= MAIN MENU ==========
def main():
    print("=== TIME SERVER PROGRAM ===")
    print("1. Run as Server")
    print("2. Run as Client")
    choice = input("Choose mode (1/2): ")

    if choice == "1":
        server = Server()
        server.start()
    elif choice == "2":
        run_client()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
