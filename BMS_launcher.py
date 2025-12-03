#!/usr/bin/env python3

"""
BMS Launcher — Tahap 2
Fokus: Deteksi OS + Setup Virtual Environment + Install Dependencies
"""

import os
import subprocess
import sys
from BMS_detect import detect, pretty_print

# ------------------------------------------------------------
# 0. LOAD ENVIRONMENT INFO
# ------------------------------------------------------------
env = detect()

print("=== BMS Environment Info ===")
pretty_print(env)
print("")


# ------------------------------------------------------------
# 1. PATH FOLDER PROJECT
# ------------------------------------------------------------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, "venv")
PYTHON_EXEC = sys.executable

print(f"[i] PROJECT_DIR : {PROJECT_DIR}")
print(f"[i] VENV_DIR    : {VENV_DIR}")
print("")


# ------------------------------------------------------------
# 2. FUNGSI SISTEM
# ------------------------------------------------------------
def run(cmd: str):
    """Jalankan command shell dengan print, aman untuk semua OS."""
    print(f"[cmd] {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("[!] Error menjalankan command!")
    return result.returncode


def create_venv():
    print("[+] Membuat Virtual Environment...")
    run(f"{PYTHON_EXEC} -m venv venv")


def install_requirements():
    req = os.path.join(PROJECT_DIR, "requirements.txt")

    # Tidak ada requirements.txt
    if not os.path.exists(req):
        print("[!] requirements.txt tidak ditemukan.")
        return

    print("[+] Upgrade pip...")
    run(f"{os.path.join(VENV_DIR, 'bin', 'python')} -m pip install --upgrade pip setuptools wheel")

    print("[+] Install dependencies...")
    run(f"{os.path.join(VENV_DIR, 'bin', 'python')} -m pip install -r requirements.txt")


# ------------------------------------------------------------
# 3. CEK & BUAT VENV
# ------------------------------------------------------------
if not os.path.exists(VENV_DIR):
    create_venv()
else:
    print("[✓] venv ditemukan.")

print("")


# ------------------------------------------------------------
# 4. INSTALL REQUIREMENTS
# ------------------------------------------------------------
install_requirements()

print("")
print("=== Tahap 2 selesai — Environment siap ===")
print("")


# ============================================================
# 5. MODE SERVER (Tahap 3)
# ============================================================

def get_python_in_venv():
    """Mencari python di dalam venv otomatis untuk semua OS."""
    # Windows
    win_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    # Linux / Mac / Termux
    unix_path = os.path.join(VENV_DIR, "bin", "python")

    if os.path.exists(win_path):
        return win_path
    return unix_path


VENV_PY = get_python_in_venv()


# ------------------------------------------------------------
# MODE: DEVELOPMENT
# ------------------------------------------------------------
def run_development():
    print("=== MODE DEVELOPMENT ===")

    # Di Linux: gunakan gunicorn jika ada
    if env["os"] == "linux" and env["has_gunicorn"]:
        cmd = f"{VENV_PY} -m gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 BMS:create_app()"
        print("[i] Server Development: Gunicorn (Linux)")
    
    # Non-Linux pakai waitress
    else:
        cmd = f"{VENV_PY} -m waitress --listen=0.0.0.0:5000 BMS:create_app"
        print("[i] Server Development: Waitress (Cross-platform)")

    run(cmd)

# ============================================================
# 5 — SUPERVISOR INTEGRASI (LINUX ONLY)
# ============================================================

def setup_supervisor():
    if env["os"] != "linux":
        print("[!] Supervisor hanya tersedia di Linux.")
        return

    print("=== Setup Supervisor ===")

    SUPERVISOR_CONF = "/etc/supervisor/conf.d/BMS.conf"
    LOG_DIR = os.path.join(PROJECT_DIR, "logs")

    # Buat folder logs jika belum ada
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print("[+] Folder logs dibuat.")

    # Path python di venv
    supervisor_python = VENV_PY

    config = f"""
[program:BMS]
directory={PROJECT_DIR}
command={supervisor_python} -m gunicorn -w 3 --threads 3 -b 127.0.0.1:5000 BMS:create_app()
autostart=true
autorestart=true
stderr_logfile={LOG_DIR}/gunicorn_err.log
stdout_logfile={LOG_DIR}/gunicorn_out.log
environment=PATH="{os.path.join(PROJECT_DIR, 'venv', 'bin')}"
"""

    # Tulis file config
    with open("BMS_supervisor_temp.conf", "w") as f:
        f.write(config)

    print("[+] Membuat file supervisor...")
    run(f"sudo cp BMS_supervisor_temp.conf {SUPERVISOR_CONF}")
    os.remove("BMS_supervisor_temp.conf")

    print("[+] Reload supervisor...")
    run("sudo supervisorctl reread")
    run("sudo supervisorctl update")

    print("[+] Start BMS process...")
    run("sudo supervisorctl start BMS")

    print("[✓] Supervisor berhasil dikonfigurasi.")

# ------------------------------------------------------------
# MODE: PRODUCTION
# ------------------------------------------------------------
# ============================================================
# 4.1 — GENERATE NGINX CONFIG (LINUX ONLY)
# ============================================================

def generate_nginx_config():
    nginx_path = "/etc/nginx/sites-available/BMS.conf"
    nginx_enabled = "/etc/nginx/sites-enabled/BMS.conf"

    STATIC_DIR = os.path.join(PROJECT_DIR, "app", "static")

    config = f"""
server {{
    listen 80;
    server_name _;

    access_log /var/log/nginx/bms_access.log;
    error_log  /var/log/nginx/bms_error.log;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /static {{
        alias {STATIC_DIR};
        try_files $uri =404;
        expires 30d;
    }}
}}
"""

    print("[+] Membuat konfigurasi NGINX...")

    # Tulis file ke sites-available
    try:
        with open("BMS_nginx_temp.conf", "w") as f:
            f.write(config)

        # copy ke /etc/nginx
        run(f"sudo cp BMS_nginx_temp.conf {nginx_path}")
        run(f"sudo ln -sf {nginx_path} {nginx_enabled}")

        os.remove("BMS_nginx_temp.conf")
        print("[✓] Konfigurasi NGINX berhasil dibuat.")

    except Exception as e:
        print("[!] Gagal membuat konfigurasi NGINX:", e)


# ============================================================
# 4.2 — RELOAD NGINX
# ============================================================

def reload_nginx():
    print("[+] Testing konfigurasi nginx...")
    run("sudo nginx -t")

    print("[+] Restarting nginx...")
    run("sudo systemctl restart nginx")

    print("[✓] Nginx berhasil dijalankan.")
def run_production():
    print("=== MODE PRODUCTION ===")

    # Jika Linux → NGINX + Gunicorn
    if env["os"] == "linux":

        # Buat config nginx otomatis
        generate_nginx_config()
        reload_nginx()

        # Jalankan Gunicorn
        cmd = (
            f"{VENV_PY} -m gunicorn -w 3 --threads 3 "
            f"-b 127.0.0.1:5000 BMS:create_app()"
        )
        print("[i] Production menggunakan Gunicorn + NGINX (Linux)")

    else:
        # Selain Linux → fallback ke waitress
        cmd = f"{VENV_PY} -m waitress --listen=0.0.0.0:5000 BMS:create_app"
        print("[i] Production fallback (Waitress non-Linux)")

    run(cmd)
# ------------------------------------------------------------
# 6. MENU MODE JALAN
# ------------------------------------------------------------

# ============================================================
# 5 — SUPERVISOR INTEGRASI (LINUX ONLY)
# ============================================================

def show_menu():
    print("Pilih Mode:")
    print("1) Development")
    print("2) Production")
    print("3) Info Environment")
    print("4) Setup Supervisor (Linux)")
    print("5) Exit")
    print("")

    pilih = input("Pilihan [1-5]: ").strip()

    if pilih == "1":
        run_development()

    elif pilih == "2":
        run_production()

    elif pilih == "3":
        pretty_print(env)

    elif pilih == "4":
        setup_supervisor()

    elif pilih == "5":
        print("Keluar...")
        sys.exit(0)

    else:
        print("Pilihan tidak valid.")

# ============================================================
# JALANKAN MENU
# ============================================================
show_menu()

print("")
print("=== Tahap 3 selesai — Server berjalan ===")