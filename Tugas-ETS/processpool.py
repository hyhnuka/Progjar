
#!/usr/bin/env python3
import os, socket, json, base64, logging
from concurrent.futures import ProcessPoolExecutor

PORT       = 7777
DATA_DIR   = "server_storage"
WORKERS    = int(os.getenv("WORKER_LIMIT", "5"))
MSG_TERM   = b"\r\n\r\n"

os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

def handler(fd):
    conn=socket.fromfd(fd,socket.AF_INET,socket.SOCK_STREAM)
    try:
        buf=b""
        while MSG_TERM not in buf:
            ch=conn.recv(1024*1024)
            if not ch: break
            buf+=ch
        msg=buf.split(MSG_TERM)[0].decode()
        parts=msg.split(" ",2); cmd=parts[0].upper()
        if cmd=="LIST":
            resp={"status":"OK","files":os.listdir(DATA_DIR)}
        elif cmd=="UPLOAD" and len(parts)==3:
            fn, data=parts[1],base64.b64decode(parts[2])
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
    conn.sendall(json.dumps(resp).encode()+MSG_TERM)
    conn.close(); os.close(fd)

def main():
    s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind(("",PORT)); s.listen()
    logging.info(f"ProcessPool server on {PORT}, workers={WORKERS}")
    with ProcessPoolExecutor(max_workers=WORKERS) as exe:
        while True:
            conn,_=s.accept()
            fd=os.dup(conn.fileno()); exe.submit(handler,fd)
            conn.close()

if __name__=="__main__":
    main()
