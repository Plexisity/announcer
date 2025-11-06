
import os
import subprocess
import time

# The EXE name is randomly generated

RUN_CHECK_INTERVAL = 1  # seconds
EXE_PATH = r"C:\announcer\index.exe"
UPDATE_EXE = os.path.join(os.path.dirname(EXE_PATH), "update.exe")

def is_index_running():
    """Return True if index.exe is present in the tasklist."""
    try:
        out = os.popen('tasklist').read()
    except Exception:
        return False
    for line in out.strip().splitlines():
        if "index.exe" in line.lower():
            return True
    return False

def start_index():
    """Start the index.exe process if the file exists."""
    if not os.path.exists(EXE_PATH):
        print(f"Executable not found: {EXE_PATH}")
        return False
    try:
        # Preferred on Windows
        os.startfile(EXE_PATH)
        return True
    except Exception:
        try:
            # Fallback to subprocess
            subprocess.Popen([EXE_PATH], shell=False)
            return True
        except Exception as e:
            print(f"Failed to start {EXE_PATH}: {e}")
            #if path does not exist start update.exe in same directory instead
            if os.path.exists(UPDATE_EXE):
                try:
                    os.startfile(UPDATE_EXE)
                    return True
                except Exception as e:
                    print(f"Failed to start {UPDATE_EXE}: {e}")
            return False

def main():
    while True:
        if not is_index_running():
            started = start_index()
            if started:
                print("index.exe started")
            else:
                print("Could not start index.exe")
        time.sleep(RUN_CHECK_INTERVAL)
        
