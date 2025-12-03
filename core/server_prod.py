# core/server_prod.py
from core.nginx_tools import generate_nginx_config, reload_nginx
from core.system_tools import run

def run_production(env: dict, venv_python: str, project_dir: str):
    print("=== PRODUCTION MODE ===")
    if env.get("os") == "linux":
        print("[i] Menyiapkan NGINX untuk production...")
        generate_nginx_config(project_dir)
        reload_nginx()
        cmd = f"{venv_python} -m gunicorn -w 3 --threads 3 -b 127.0.0.1:5000 app:create_app()"
        print("[i] Menjalankan Gunicorn (production).")
    else:
        cmd = f"{venv_python} -m waitress --listen=0.0.0.0:5000 BMS:create_app"
        print("[i] Menjalankan Waitress (production fallback).")
    run(cmd)