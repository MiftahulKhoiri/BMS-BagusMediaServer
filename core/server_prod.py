# core/server_prod.py
import socket
from core.nginx_tools import generate_nginx_config, reload_nginx
from core.system_tools import run


def get_ip_address():
    """Ambil IP address utama yang bisa diakses di LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def run_production(env: dict, venv_python: str, project_dir: str):
    print("=== PRODUCTION MODE ===")

    # Ambil IP server
    server_ip = get_ip_address()

    # Jika Linux / Raspberry Pi → Gunicorn + NGINX
    if env.get("os") == "linux" and not env.get("is_termux"):
        print(f"[✓] Server akan berjalan di:     http://{server_ip}")
        print(f"[✓] Backend (Gunicorn) di:       http://127.0.0.1:5000")
        print("[i] Menyiapkan konfigurasi NGINX...")

        generate_nginx_config(project_dir)
        reload_nginx()

        cmd = (
            f"{venv_python} -m gunicorn "
            f"-w 3 --threads 3 "
            f"-b 127.0.0.1:5000 "
            f"wsgi:application"
        )

        print("[i] Menjalankan Gunicorn (production)...")

    else:
        # Termux, Windows, macOS → Waitress
        print(f"[✓] Server berjalan di:          http://{server_ip}:5000")
        print("[i] Menjalankan Waitress (fallback production).")

        cmd = (
            f"{venv_python} -m waitress "
            f"--listen=0.0.0.0:5000 "
            f"wsgi:application"
        )

    print(f"[cmd] {cmd}")
    run(cmd)

    print("\n=== Production Server Aktif ===")
    print(f"Akses melalui browser: http://{server_ip}")
    print("================================\n")