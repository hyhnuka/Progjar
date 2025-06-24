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
