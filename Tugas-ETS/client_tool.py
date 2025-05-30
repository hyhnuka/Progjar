# #client_tool.py
# import socket, json, base64, sys, os

# SERVER_ADDR = ("127.0.0.1", 7777)
# DELIM = "\r\n\r\n"

# def send_command(cmd):
#     with socket.socket() as s:
#         s.connect(SERVER_ADDR)
#         s.sendall((cmd + DELIM).encode())
#         buff = ""
#         while DELIM not in buff:
#             data = s.recv(1024*1024)
#             if not data:
#                 break
#             buff += data.decode()
#     return json.loads(buff.split(DELIM)[0])

# def list_files():
#     resp = send_command("LIST")
#     print("Daftar file di server:")
#     for item in resp.get("files", []):
#         print("-", item)

# def upload_file(filename):
#     if not os.path.exists(filename):
#         print(f"File '{filename}' tidak ditemukan.")
#         return
#     with open(filename, "rb") as f:
#         data = f.read()
#     b64data = base64.b64encode(data).decode()
#     resp = send_command(f"UPLOAD {filename} {b64data}")
#     print(resp)

# def download_file(filename):
#     resp = send_command(f"GET {filename}")
#     if resp.get("status") == "OK":
#         data = base64.b64decode(resp["file_data"])
#         with open(f"download_{filename}", "wb") as f:
#             f.write(data)
#         print(f"Download berhasil, ukuran file {len(data)} bytes")
#     else:
#         print("Download gagal:", resp)

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage:")
#         print(" python client_tool.py list")
#         print(" python client_tool.py upload <filename>")
#         print(" python client_tool.py download <filename>")
#         sys.exit(1)

#     command = sys.argv[1].lower()
#     if command == "list":
#         list_files()
#     elif command == "upload" and len(sys.argv) == 3:
#         upload_file(sys.argv[2])
#     elif command == "download" and len(sys.argv) == 3:
#         download_file(sys.argv[2])
#     else:
#         print("Perintah tidak valid atau argumen kurang.")

import socket, json, base64, os, sys

SERVER_ADDR = ("127.0.0.1", 7777)
DELIM       = "\r\n\r\n"

def send_command(cmd: str) -> dict:
    with socket.socket() as s:
        s.connect(SERVER_ADDR)
        s.sendall((cmd + DELIM).encode())
        buf = ""
        while DELIM not in buf:
            chunk = s.recv(1024*1024)
            if not chunk:
                break
            buf += chunk.decode()
    return json.loads(buf.split(DELIM)[0])

def list_files() -> list[str]:
    resp = send_command("LIST")
    return resp.get("files", [])

def upload_file(path: str) -> tuple[bool,int]:
    if not os.path.exists(path):
        return False, 0
    data = open(path, "rb").read()
    resp = send_command(f"UPLOAD {os.path.basename(path)} {base64.b64encode(data).decode()}")
    ok = resp.get("status") == "OK"
    return ok, len(data) if ok else 0

def download_file(name: str) -> tuple[bool,int]:
    resp = send_command(f"GET {name}")
    if resp.get("status") != "OK":
        return False, 0
    data = base64.b64decode(resp["file_data"])
    with open(f"download_{name}", "wb") as f:
        f.write(data)
    return True, len(data)

if __name__=="__main__":
    cmd = sys.argv[1].lower() if len(sys.argv)>1 else "help"
    if cmd=="list":
        print("\n".join(list_files()))
    elif cmd=="upload" and len(sys.argv)==3:
        ok, b = upload_file(sys.argv[2]); print("OK" if ok else "FAIL", b, "bytes")
    elif cmd=="download" and len(sys.argv)==3:
        ok, b = download_file(sys.argv[2]); print("OK" if ok else "FAIL", b, "bytes")
    else:
        print("Usage: client_tool.py [list|upload <file>|download <file>]")
