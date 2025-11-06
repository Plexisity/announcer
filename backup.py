import os
import subprocess
import time

# exe is named MRSC and the icon is default

def is_index_running():
    out = os.popen('tasklist').read()
    for line in out.strip().splitlines()[3:]:
        if "index.exe" in line or "update.exe" in line:
            print("index.exe or update.exe is running")
            return True
    print("index.exe or update.exe are not running")
    return False

def open_index():
    print("Starting index.exe")
    # Windows: os.startfile is simplest; fall back to subprocess if not available
    exe_path = r"C:\announcer\index.exe"
    upd_path = r"C:\announcer\update.exe"
    try:
        os.startfile(exe_path)
    except Exception:
        try:
            subprocess.Popen(exe_path, shell=False)
        except Exception:
            print("Failed to start index.exe, trying update.exe")
            subprocess.Popen([upd_path], shell=False)

def main(poll_interval=1):
    while True:
        if not is_index_running():
            open_index()
        time.sleep(poll_interval)

if __name__ == "__main__":
    main()