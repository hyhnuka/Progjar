# #!/usr/bin/env python3
# #stress_test.py
# import os, time, json
# from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
# import base64
# import socket

# SERVER_ADDR = ("127.0.0.1", 7777)
# DELIM = "\r\n\r\n"

# def send_command(command):

#     with socket.socket() as s:
#         s.connect(SERVER_ADDR)
#         s.sendall((command + DELIM).encode())
#         buff = ""
#         while DELIM not in buff:
#             data = s.recv(1024*1024)
#             if not data:
#                 break
#             buff += data.decode()
#     return json.loads(buff.split(DELIM)[0])

# def client_list():
#     resp = send_command("LIST")
#     if resp.get("status") == "OK":
#         return resp["files"]
#     return []

# def client_upload(filepath):
#     with open(filepath, "rb") as f:
#         data = f.read()
#     b64data = base64.b64encode(data).decode()
#     filename = os.path.basename(filepath)
#     resp = send_command(f"UPLOAD {filename} {b64data}")
#     return resp.get("status") == "OK"

# def client_download(filename):
#     resp = send_command(f"GET {filename}")
#     if resp.get("status") == "OK":
#         data = base64.b64decode(resp["file_data"])
#         with open(f"download_{filename}", "wb") as f:
#             f.write(data)
#         return True, len(data)
#     return False, 0

# # Generate dummy file if not exists
# def prepare_file(size_mb):
#     fname = f"dummy_{size_mb}MB.bin"
#     if not os.path.exists(fname):
#         with open(fname, "wb") as f:
#             f.write(os.urandom(size_mb * 1024 * 1024))
#     return fname

# def worker_task(_op, fname):
#     start = time.time()
#     if _op == "upload":
#         success = client_upload(fname)
#         bytes_transferred = os.path.getsize(fname) if success else 0
#     else:
#         success, bytes_transferred = client_download(fname)
#     elapsed = time.time() - start
#     return {"success": success, "time": elapsed, "bytes": bytes_transferred}

# def main():
#     operation = os.getenv("STRESS_OP", "download")  # "download" or "upload"
#     file_size = int(os.getenv("FILE_SIZE_MB", "10"))
#     pool_type = os.getenv("CLIENT_POOL_TYPE", "thread")  # "thread" or "process"
#     client_count = int(os.getenv("CLIENT_POOL", "1"))

#     fname = prepare_file(file_size)

#     Executor = ThreadPoolExecutor if pool_type == "thread" else ProcessPoolExecutor

#     with Executor(max_workers=client_count) as executor:
#         results = list(executor.map(lambda _: worker_task(operation, fname), range(client_count)))

#     total_time = sum(r["time"] for r in results)
#     total_bytes = sum(r["bytes"] for r in results)
#     success_count = sum(1 for r in results if r["success"])
#     fail_count = client_count - success_count

#     output = {
#         "clients": client_count,
#         "pool_type": pool_type,
#         "operation": operation,
#         "file_size_MB": file_size,
#         "total_duration_sec": round(total_time, 3),
#         "throughput_Bps": int(total_bytes / total_time) if total_time > 0 else 0,
#         "successes": success_count,
#         "failures": fail_count,
#     }
#     print(json.dumps(output))

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
#!/usr/bin/env python3
import os
import sys
import time
import csv
import signal
import subprocess
import base64
from itertools import product
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from client_tool import upload_file, download_file, list_files

# server_mode → (script, env_var)
SERVER_MODES = {
    "thread":  ("threadpool.py",  "MAX_CLIENTS"),
    "process": ("processpool.py", "WORKER_LIMIT"),
}

SERVER_WORKERS = [1, 5, 50]
CLIENT_WORKERS = [1, 5, 50]
OPERATIONS     = ["download", "upload"]
FILE_SIZES_MB  = [10, 50, 100]  # in MB

OUTPUT_CSV     = "results.csv"
PORT           = 7777

def ensure_dummy():
    for mb in FILE_SIZES_MB:
        fn = f"dummy_{mb}MB.bin"
        if not os.path.exists(fn):
            with open(fn, "wb") as f:
                f.write(os.urandom(mb * 1024 * 1024))

def launch_server(mode, workers):
    script, env_var = SERVER_MODES[mode]
    env = os.environ.copy()
    env[env_var] = str(workers)
    p = subprocess.Popen(
        [sys.executable, script],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )
    time.sleep(1)  # give it time to bind
    return p

def kill_server(proc):
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc.wait()

def measure_one(op, filepath, client_pool):
    """
    Returns (total_time, throughput, client_success, client_fail)
    """
    start = time.time()
    ok = 0
    fail = 0
    total_bytes = 0

    # always use thread pool for client side; you could switch to ProcessPoolExecutor if desired
    with ThreadPoolExecutor(max_workers=client_pool) as exe:
        futures = []
        for _ in range(client_pool):
            if op == "upload":
                futures.append(exe.submit(upload_file, filepath))
            else:  # download
                # ensure file exists on server first
                # if you want to test list, call list_files() here
                futures.append(exe.submit(download_file, os.path.basename(filepath)))

        for f in futures:
            success, b = f.result()
            if success:
                ok += 1
                total_bytes += b
            else:
                fail += 1

    duration = time.time() - start
    thrpt = int(total_bytes / duration) if duration > 0 else 0
    return round(duration, 3), thrpt, ok, fail

def main():
    ensure_dummy()
    combos = list(product(SERVER_MODES.keys(), SERVER_WORKERS,
                         OPERATIONS, FILE_SIZES_MB, CLIENT_WORKERS))
    # prepare CSV
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "No","Operation","Volume","ClientPool","ServerPool",
            "Time_s","Throughput_Bps","ClientSucc","ClientFail","ServerSucc","ServerFail"
        ])

        idx = 1
        total = len(combos)
        for mode, srv_w, op, vol, cli_w in combos:
            print(f"[{idx}/{total}] mode={mode} srv_w={srv_w} op={op} vol={vol} cli_w={cli_w}")
            # 1) start server
            srv = launch_server(mode, srv_w)
            path = f"dummy_{vol}MB.bin"

            # 2) measure
            t, thr, cs, cf = measure_one(op, path, cli_w)

            # 3) stop server
            kill_server(srv)

            # 4) record (server success/fail = client success/fail)
            w.writerow([idx, op, f"{vol}MB", cli_w, srv_w, t, thr, cs, cf, cs, cf])
            f.flush()

            idx += 1

    print(f"✅ All done! See {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

