import sys
import socket
import json
import logging
import ssl
import os

# server_address = ('www.its.ac.id', 443)
# server_address = ('www.ietf.org',443)

server_address = ('172.16.16.101', 8885)  # untuk thread pool
server_address = ('172.16.16.101', 8889)  # untuk process pool

def make_socket(destination_address='172.16.16.101', port=12000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"Connecting to {server_address}")
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"Socket error: {str(ee)}")

def make_secure_socket(destination_address='172.16.16.101', port=10000):
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"Connecting to {server_address} with SSL")
        sock.connect(server_address)
        secure_socket = context.wrap_socket(sock, server_hostname=destination_address)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"Secure socket error: {str(ee)}")

def send_command(command_str, is_secure=False):
    host, port = server_address
    sock = make_secure_socket(host, port) if is_secure else make_socket(host, port)

    try:
        logging.warning(f"Sending command: {command_str.strip()}")
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(2048)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        logging.warning("Data received from server")
        return data_received
    except Exception as ee:
        logging.warning(f"Error receiving data: {str(ee)}")
        return False

def send_list():
    cmd = """GET /list HTTP/1.0\r\n\r\n"""
    return send_command(cmd, is_secure=False)

def send_upload(filename, content):
    content_bytes = content.encode()
    content_length = len(content_bytes)
    cmd = f"""POST /upload HTTP/1.0\r\nFilename: {filename}\r\nContent-Length: {content_length}\r\n\r\n{content}"""
    return send_command(cmd, is_secure=False)

def send_delete(filename):
    cmd = f"""DELETE /delete?file={filename} HTTP/1.0\r\n\r\n"""
    return send_command(cmd, is_secure=False)

def show_menu():
    while True:
        print("\n Pilih Aksi:")
        print("1. Lihat daftar file")
        print("2. Upload file")
        print("3. Hapus file")
        print("4. Keluar")
        pilihan = input("Pilih: ").strip()

        if pilihan == "1":
            hasil = send_list()
            print("Daftar file di server:\n", hasil)
        elif pilihan == "2":
            filepath = input("Masukkan nama file yang akan diupload: ").strip()
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                filename = os.path.basename(filepath)
                hasil = send_upload(filename, content)
                print("Upload response:\n", hasil)
            else:
                print("File tidak ditemukan.")
        elif pilihan == "3":
            filename = input("Masukkan nama file yang akan dihapus: ").strip()
            hasil = send_delete(filename)
            print("Delete response:\n", hasil)
        elif pilihan == "4":
            print("Keluar.")
            break
        else:
            print("Pilihan tidak valid.")


if __name__ == '__main__':
    show_menu()
