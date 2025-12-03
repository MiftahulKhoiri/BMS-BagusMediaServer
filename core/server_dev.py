# core/server_dev.py
from core.system_tools import run

def run_development(env: dict, venv_python: str):
    """
    Jalankan server development:
    - Linux + gunicorn -> gunakan gunicorn
    - Lainnya -> waitress
    """
    print("=== DEVELOPMENT MODE ===")
    if env.get("os") == "linux" and env.get("has_gunicorn"):
        cmd = f"{venv_python} -m gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 BMS:create_app()"
        print("[i] Menjalankan Gunicorn (development).")
    else:
        cmd = f"{venv_python} -m waitress --listen=0.0.0.0:5000 app:create_app"
        print("[i] Menjalankan Waitress (development fallback).")
    run(cmd)