
#!/usr/bin/env python3
import os, socket, json, base64, logging
from concurrent.futures import ThreadPoolExecutor

PORT       = 7777
DATA_DIR   = "server_storage"
WORKERS    = int(os.getenv("MAX_CLIENTS", "5"))
MSG_TERM   = b"\r\n\r\n"

os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

def handle(sock: socket.socket):
    try:
        buf = b""
        while MSG_TERM not in buf:
            chunk = sock.recv(1024*1024)
            if not chunk: break
            buf += chunk
        msg = buf.split(MSG_TERM)[0].decode()
        parts = msg.split(" ",2)
        cmd = parts[0].upper()
        if cmd=="LIST":
            resp={"status":"OK","files":os.listdir(DATA_DIR)}
        elif cmd=="UPLOAD" and len(parts)==3:
            fn, data = parts[1], base64.b64decode(parts[2])
            open(os.path.join(DATA_DIR,fn),"wb").write(data)
            resp={"status":"OK"}
        elif cmd=="GET" and len(parts)>=2:
            fn=parts[1]; path=os.path.join(DATA_DIR,fn)
            if os.path.exists(path):
                resp={"status":"OK","file_data":base64.b64encode(open(path,"rb").read()).decode()}
            else:
                resp={"status":"ERROR","message":"not found"}
        else:
            resp={"status":"ERROR","message":"bad cmd"}
    except Exception as e:
        logging.error(e); resp={"status":"ERROR","message":str(e)}
    sock.sendall(json.dumps(resp).encode()+MSG_TERM)
    sock.close()

def main():
    srv=socket.socket(); srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    srv.bind(("",PORT)); srv.listen()
    logging.info(f"ThreadPool server on {PORT}, workers={WORKERS}")
    with ThreadPoolExecutor(max_workers=WORKERS) as exe:
        while True:
            s,_=srv.accept(); exe.submit(handle,s)

if __name__=="__main__":
    main()
