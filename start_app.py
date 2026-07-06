"""
start_app.py
------------
Convenience launcher: starts the FastAPI backend in the background,
then opens the React frontend URL in the browser.

Usage:
    python start_app.py
"""

import io
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ── Fix emoji output on Windows (cp1252 console) ────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

API_PORT  = 8000
UI_PORT   = 5173
API_URL   = f"http://localhost:{API_PORT}"
UI_URL    = f"http://localhost:{UI_PORT}"
ROOT      = Path(__file__).parent
UI_DIR    = ROOT / "ui"

def run():
    print("\n🚀  AI Startup Funding Intelligence Assistant")
    print("=" * 50)
    print(f"   Backend (FastAPI) : {API_URL}")
    print(f"   Frontend (React)  : {UI_URL}")
    print("=" * 50)
    print("\n⚡  Starting services…\n")

    # Start FastAPI backend (no --reload: it spawns multiple workers that
    # fight over loading the embedding model and block the server port)
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.server:app",
         "--port", str(API_PORT), "--workers", "1"],
        cwd=str(ROOT),
    )

    # Check if UI dependencies need to be installed
    node_modules = UI_DIR / "node_modules"
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    
    if not node_modules.exists():
        print("   Detected missing Node modules. Installing React dependencies...")
        subprocess.run([npm, "install"], cwd=str(UI_DIR), check=True)
        print("   Dependencies installed!\n")

    # Start Vite dev server

    frontend = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=str(UI_DIR),
    )

    # Wait for the backend to be ready before opening the browser
    import urllib.request
    print("   Waiting for backend to be ready", end="", flush=True)
    for _ in range(30):  # up to 30 seconds
        time.sleep(1)
        print(".", end="", flush=True)
        try:
            urllib.request.urlopen(f"{API_URL}/", timeout=2)
            print(" Ready!")
            break
        except Exception:
            pass
    else:
        print(" (timed out — opening anyway)")

    print(f"\n🌐  Opening browser at {UI_URL} ...\n")
    webbrowser.open(UI_URL)

    print("Press Ctrl+C to stop both servers.\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\n\n🛑  Stopping servers…")
        backend.terminate()
        frontend.terminate()
        print("Done. Goodbye! 👋\n")


if __name__ == "__main__":
    run()
