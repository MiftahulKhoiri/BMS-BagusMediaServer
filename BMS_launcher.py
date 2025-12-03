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

# ============================================================
# 6 — SYSTEM MONITORING (CROSS PLATFORM)
# ============================================================

import time
import socket

def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "Unknown"


def get_cpu_temp():
    if env["is_rpi"] and env["has_vcgencmd"]:
        out = os.popen("vcgencmd measure_temp").read().strip()
        return out.replace("temp=", "")
    return "Not supported"


def get_uptime():
    if env["os"] == "linux":
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
            hours = seconds / 3600
            return f"{hours:.2f} jam"
    return "Not supported"


def get_cpu_load():
    if env["os"] == "linux":
        load1, load5, load15 = os.getloadavg()
        return f"{load1}, {load5}, {load15}"
    return "Not supported"


def get_memory_usage():
    if env["os"] == "linux":
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, val = line.split(":")
                meminfo[key] = int(val.strip().split()[0])
        total = meminfo["MemTotal"] // 1024
        free = meminfo["MemAvailable"] // 1024
        used = total - free
        return f"{used}MB / {total}MB"
    return "Not supported"


def check_port_5000():
    import socket
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect(("127.0.0.1", 5000))
        s.close()
        return "Aktif"
    except:
        return "Mati"


def check_gunicorn():
    if env["os"] != "linux":
        return "Not available"
    out = os.popen("pgrep gunicorn").read().strip()
    return "Aktif" if out else "Mati"


def check_supervisor():
    if env["os"] != "linux":
        return "Not available"
    out = os.popen("sudo supervisorctl status BMS").read().strip()
    if "RUNNING" in out:
        return "Running"
    return "Stopped / Not installed"


def monitoring():
    print("====== BMS SYSTEM MONITORING ======")
    print(f"OS                 : {env['os']}")
    print(f"IP Address         : {get_ip()}")
    print(f"CPU Temperature    : {get_cpu_temp()}")
    print(f"CPU Load (1/5/15)  : {get_cpu_load()}")
    print(f"Memory Usage       : {get_memory_usage()}")
    print(f"Uptime             : {get_uptime()}")
    print("-----------------------------------")
    print(f"Port 5000 Status   : {check_port_5000()}")
    print(f"Gunicorn Status    : {check_gunicorn()}")
    print(f"Supervisor Status  : {check_supervisor()}")
    print("===================================")

# ============================================================
# 7 — AUTO UPDATE SYSTEM (Git + Dependencies + Restart)
# ============================================================

def git_available():
    return shutil.which("git") is not None


def git_pull():
    print("[i] Menarik update dari GitHub...")
    if not git_available():
        print("[!] Git tidak tersedia di sistem.")
        return False

    status = run("git pull")

    if status != 0:
        print("[!] Git pull gagal. Ada kemungkinan konflik perubahan.")
        return False

    print("[✓] Update berhasil.")
    return True


def has_requirements_changed():
    # Jika requirements.txt berubah setelah git pull → install lagi
    return os.path.exists("requirements.txt")


def restart_services():
    print("[i] Restarting services...")

    if env["os"] == "linux":
        print("[i] Memberhentikan Gunicorn...")
        run("pkill gunicorn")

        print("[i] Restart Supervisor (jika ada)...")
        run("sudo supervisorctl restart BMS")

    else:
        print("[i] Non-Linux: tidak ada service yang perlu di-restart otomatis.")

    print("[✓] Service berhasil direstart.")


def auto_update():
    print("====== BMS AUTO UPDATE ======")

    # 1. Git Pull
    if not git_pull():
        print("[!] Update dihentikan akibat kegagalan git.")
        return

    # 2. Install dependencies
    if has_requirements_changed():
        print("[i] Menginstall ulang dependencies...")
        install_requirements()

    # 3. Restart server
    restart_services()

    print("====== UPDATE SELESAI ======")

# ============================================================
# 8 — AUTO REPAIR SYSTEM (Cross Platform & Linux Enhancements)
# ============================================================

def repair_gunicorn():
    print("[i] Memperbaiki Gunicorn...")

    # Hentikan Gunicorn
    run("pkill gunicorn")

    # Hapus PID file jika ada
    if os.path.exists("/tmp/gunicorn.pid"):
        run("sudo rm /tmp/gunicorn.pid")

    print("[✓] Gunicorn diperbaiki.")


def repair_port_5000():
    print("[i] Membersihkan port 5000...")

    if env["os"] == "linux":
        run("sudo fuser -k 5000/tcp")
    else:
        # Cross OS method
        run("kill -9 $(lsof -t -i:5000)")  # Windows mungkin skip
    print("[✓] Port 5000 dibersihkan.")


def repair_supervisor():
    if env["os"] != "linux":
        print("[!] Supervisor tidak tersedia di OS ini.")
        return

    print("[i] Memperbaiki Supervisor...")

    run("sudo supervisorctl reread")
    run("sudo supervisorctl update")
    run("sudo supervisorctl restart BMS")

    print("[✓] Supervisor diperbaiki.")


def repair_nginx():
    if env["os"] != "linux":
        print("[!] Nginx hanya tersedia di Linux.")
        return

    print("[i] Memeriksa konfigurasi Nginx...")
    run("sudo nginx -t")

    print("[i] Restarting Nginx...")
    run("sudo systemctl restart nginx")

    print("[✓] Nginx diperbaiki.")


def repair_permissions():
    print("[i] Menyetel ulang permission folder proyek...")
    run(f"sudo chmod -R 755 {PROJECT_DIR}")
    print("[✓] Permission diperbaiki.")


def auto_repair():
    print("====== BMS AUTO REPAIR ======")

    # 1. Perbaiki Gunicorn
    repair_gunicorn()

    # 2. Bersihkan port 5000
    repair_port_5000()

    # 3. Perbaiki Supervisor (Linux only)
    repair_supervisor()

    # 4. Perbaiki Nginx (Linux only)
    repair_nginx()

    # 5. Perbaiki permission
    repair_permissions()

    print("====== PERBAIKAN SELESAI ======")
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
    print("6) Monitoring System")
    print("7) Update System")
    print("8) Auto Repair System")
    print("")

    pilih = input("Pilihan [1-8]: ").strip()

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

    elif pilih == "6":
        monitoring()

    elif pilih == "7":
        auto_update()

    elif pilih == "8":
        auto_repair()

    else:
        print("Pilihan tidak valid.")

# ============================================================
# JALANKAN MENU
# ============================================================
show_menu()

print("")
print("=== Tahap 3 selesai — Server berjalan ===")