from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

# ...existing code...
def ProcessTheClient(connection, address):
    try:
        buffer = b""
        content_length = 0

        while True:
            data = connection.recv(1024)
            if not data:
                break
            buffer += data

            if b"\r\n\r\n" in buffer:
                header, body = buffer.split(b"\r\n\r\n", 1)
                header_lines = header.decode(errors='ignore').split("\r\n")

                for line in header_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":", 1)[1].strip())
                        break

                # Jika ada body, lanjutkan baca hingga lengkap
                while len(body) < content_length:
                    more = connection.recv(1024)
                    if not more:
                        break
                    body += more

                full_request = header + b"\r\n\r\n" + body
                break  # Selesai membaca

        # Jika tidak ada header sama sekali
        if not buffer:
            connection.close()
            return

        # Proses permintaan
        hasil = httpserver.proses(full_request.decode(errors='ignore'))
        connection.sendall(hasil.encode() + b"\r\n\r\n")
    except Exception as e:
        logging.warning(f"Terjadi error: {e}")
    finally:
        connection.close()

def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 8885))
	my_socket.listen(1)

	with ThreadPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				#logging.warning("connection from {}".format(client_address))
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)
				#menampilkan jumlah process yang sedang aktif
				jumlah = ['x' for i in the_clients if i.running()==True]
				print(jumlah)

def main():
	Server()

if __name__=="__main__":
	main()
