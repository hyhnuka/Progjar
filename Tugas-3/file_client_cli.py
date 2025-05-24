import socket
import json
import base64
import logging
import os

server_address = ('0.0.0.0', 7777)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = ""
        while True:
            data = sock.recv(16)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return False

def remote_list():
    command_str=f"LIST"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False


def remote_get(filename=""):
    command_str=f"GET {filename}"
    hasil = send_command(command_str)

    if (hasil['status']=='OK'):
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filename):
    try:
        with open(filename, "rb") as f:
            file_bytes = f.read()

        # Encoding base64 lalu hapus newline dan carriage return
        file_b64 = base64.b64encode(file_bytes).decode('utf-8').replace('\n', '').replace('\r', '')

        command_str = f"UPLOAD {os.path.basename(filename)} {file_b64}"
        hasil = send_command(command_str)
        if hasil['status'] == 'OK':
            print("Upload berhasil")
            return True
        else:
            print(f"Upload gagal: {hasil.get('message', '')}")
            return False
    except Exception as e:
        print(f"Error membaca file: {str(e)}")
        return False


def remote_delete(filename):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil['status'] == 'TOK':
        print("Delete berhasil")
        return True
    else:
        print(f"Delete gagal: {hasil.get('message', '')}")
        return False


if __name__ == '__main__':
    server_address = ('172.18.0.3', 7777)
    while True:
        print("\nPilih operasi:")
        print("1. List file")
        print("2. Download file")
        print("3. Upload file")
        print("4. Hapus file")
        print("5. Keluar")
        pilihan = input("Masukkan pilihan (1-5): ")

        if pilihan == '1':
            remote_list()
        elif pilihan == '2':
            fname = input("Nama file yang didownload: ").strip()
            remote_get(fname)
        elif pilihan == '3':
            path = input("Path file yang akan diupload: ").strip()
            remote_upload(path)
        elif pilihan == '4':
            fname = input("Nama file yang akan dihapus: ").strip()
            remote_delete(fname)
        elif pilihan == '5':
            print("Keluar program.")
            break
        else:
            print("Pilihan tidak valid.")

