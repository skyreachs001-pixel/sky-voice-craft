import os
import sys
import time
import socket
import argparse
import subprocess
import urllib.request
import webbrowser

# Reconfigure stdout/stderr for Windows console compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8000
SERVER_URL = f"http://127.0.0.1:{PORT}"

def is_server_running() -> bool:
    try:
        req = urllib.request.Request(f"{SERVER_URL}/api/status", headers={"User-Agent": "Launcher"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def find_browser_app_executable() -> str | None:
    """Find Microsoft Edge or Google Chrome to launch in standalone --app window mode."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def launch_app_window(url: str, mode: str):
    browser_exe = find_browser_app_executable()

    if mode == "mobile":
        # Smartphone viewport dimensions (e.g. 430 x 920 - iPhone / Android Pro)
        window_size = "440,920"
    else:
        # Full Desktop Workstation dimensions
        window_size = "1320,860"

    if browser_exe:
        try:
            cmd = [
                browser_exe,
                f"--app={url}",
                f"--window-size={window_size}",
                "--disable-features=Translate",
                "--no-first-run"
            ]
            subprocess.Popen(cmd)
            return
        except Exception:
            pass

    # Fallback to standard default browser
    webbrowser.open(url)

def main():
    parser = argparse.ArgumentParser(description="VoiceCraft Studio Launcher")
    parser.add_argument("--mode", choices=["desktop", "mobile"], default="desktop", help="App view mode: desktop or mobile")
    args = parser.parse_args()

    mode = args.mode
    target_url = f"{SERVER_URL}/?view={mode}"

    print("=" * 65)
    print(f"[*] SKY VOICE CRAFT - LAUNCHING [{mode.upper()} VERSION]")
    print("=" * 65)

    # 1. Start Server if not already running
    if not is_server_running():
        print("[*] Starting backend server on port 8000...")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app_script = os.path.join(base_dir, "app.py")

        python_exe = sys.executable
        # Launch server as a separate background process
        creationflags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        subprocess.Popen([python_exe, app_script], cwd=base_dir, creationflags=creationflags)

        # 2. Wait until server responds with 200 OK
        print("[*] Waiting for server initialization...")
        for _ in range(30):
            time.sleep(0.4)
            if is_server_running():
                print("[+] Server is online and ready!")
                break
        else:
            print("[-] Warning: Server startup took longer than usual. Opening anyway...")
    else:
        print("[+] Existing server found running!")

    # 3. Launch App Window
    print(f"[*] Opening {mode.upper()} view window ({target_url})...")
    launch_app_window(target_url, mode)
    print("[+] Done!")

if __name__ == "__main__":
    main()
