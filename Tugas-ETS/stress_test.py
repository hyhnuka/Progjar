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

    print(f"All done! See {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

