import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def start_fastapi_backend() -> subprocess.Popen:
    """Start FastAPI backend with uvicorn in a background process."""
    print("[1/2] Starting FastAPI backend with uvicorn on http://127.0.0.1:8000 ...")

    # Uses main:app as in README. If you prefer app.main:app, change here.
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError:
        print("Could not start uvicorn. Make sure 'uvicorn' is installed (pip install uvicorn).")
        sys.exit(1)

    return proc


def start_streamlit_ui() -> int:
    """Start the Streamlit UI (streamlit_app/ui.py) in the foreground."""
    print("[2/2] Starting Streamlit UI...")
    ui_path = ROOT / "streamlit_app" / "ui.py"
    if not ui_path.exists():
        print(f"Could not find {ui_path}")
        return 1

    cmd = ["streamlit", "run", str(ui_path)]

    try:
        code = subprocess.call(cmd, cwd=str(ROOT))
    except FileNotFoundError:
        print("Could not start Streamlit. Make sure 'streamlit' is installed (pip install streamlit).")
        return 1

    return code


def main() -> None:
    backend_proc = start_fastapi_backend()

    try:
        exit_code = start_streamlit_ui()
    finally:
        # Stop backend when Streamlit exits
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
