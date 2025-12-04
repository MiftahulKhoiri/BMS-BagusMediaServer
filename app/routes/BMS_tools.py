import os
import signal
import subprocess
from flask import Blueprint, request, jsonify, session
from app.routes.BMS_logger import BMS_write_log

tools = Blueprint("tools", __name__, url_prefix="/tools")

LOG_FILE = "bms_tools.log"



# ======================================================
#  HELPER — ROOT CHECK
# ======================================================

def BMS_tools_is_root():
    """Cek apakah user login sebagai ROOT"""
    return session.get("role") == "root"



# ======================================================
#  HELPER — LOGGING
# ======================================================

def BMS_tools_write_log(message):
    """Simpan log ke file tools"""
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")



# ======================================================
#  HELPER — SHELL COMMAND
# ======================================================

def BMS_tools_run(cmd):
    """Menjalankan perintah shell dan auto-log"""
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        result = output.decode()
        BMS_tools_write_log(result)
        return result
    except subprocess.CalledProcessError as e:
        err = e.output.decode()
        BMS_tools_write_log("ERROR: " + err)
        return err



# ======================================================
#  AUTO DETECT PROJECT STRUCTURE
# ======================================================

def detect_project_dir():
    """
    Mendeteksi folder project BMS secara otomatis.
    Mengambil folder paling atas (yang berisi 'app' dan 'venv').
    """
    base = os.path.dirname(os.path.abspath(__file__))      # .../app/routes
    project = os.path.abspath(os.path.join(base, "..", ".."))
    return project


def detect_venv_python(project_dir):
    """Cari python dalam virtualenv (Linux / Windows)"""
    p1 = os.path.join(project_dir, "venv/bin/python3")
    p2 = os.path.join(project_dir, "venv/Scripts/python.exe")

    if os.path.exists(p1): return p1
    if os.path.exists(p2): return p2
    return None


def detect_gunicorn(project_dir):
    """Cari gunicorn dalam virtualenv"""
    g1 = os.path.join(project_dir, "venv/bin/gunicorn")
    g2 = os.path.join(project_dir, "venv/Scripts/gunicorn.exe")

    if os.path.exists(g1): return g1
    if os.path.exists(g2): return g2
    return None


def detect_wsgi(project_dir):
    """
    Deteksi WSGI:
    1. wsgi:application (jika ada file wsgi.py)
    2. app:create_app()  → fallback universal
    """
    wsgi_file = os.path.join(project_dir, "wsgi.py")
    if os.path.exists(wsgi_file):
        return "wsgi:application"

    return "app:create_app()"



# ======================================================
#  STOP GUNICORN
# ======================================================

def stop_gunicorn():
    pid_file = "/tmp/gunicorn.pid"

    if not os.path.exists(pid_file):
        return False, "Gunicorn tidak berjalan."

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        return True, f"Gunicorn dimatikan (PID {pid})."

    except Exception as e:
        return False, f"Gagal menghentikan Gunicorn: {e}"



# ======================================================
#  STOP NGINX
# ======================================================

def stop_nginx():
    code = os.system("sudo systemctl stop nginx")
    if code == 0:
        return True, "NGINX berhasil dihentikan."
    return False, "Gagal menghentikan NGINX."



# ======================================================
#  STOP FLASK DEV SERVER
# ======================================================

def stop_flask_dev():
    try:
        func = request.environ.get("werkzeug.server.shutdown")
        if func:
            func()
            return True, "Flask dev server dimatikan."
        return False, "Flask dev server tidak aktif."
    except Exception as e:
        return False, f"Gagal menghentikan Flask dev server: {e}"



# ======================================================
#  RESTART SERVER (FULL AUTOMATIC RESTART)
# ======================================================

@tools.route("/restart")
def BMS_tools_restart():

    if not BMS_tools_is_root():
        return "Akses ditolak!"

    BMS_write_log("SERVER RESTART DIPANGGIL")

    results = {}

    # ---------------------------------------------
    # 1) Autodetect PATH
    # ---------------------------------------------
    PROJECT_DIR = detect_project_dir()
    VENV_PY     = detect_venv_python(PROJECT_DIR)
    GUNICORN    = detect_gunicorn(PROJECT_DIR)
    WSGI_TARGET = detect_wsgi(PROJECT_DIR)

    results["project"]   = PROJECT_DIR
    results["venv_python"] = VENV_PY
    results["gunicorn_bin"] = GUNICORN
    results["wsgi_entry"] = WSGI_TARGET

    if not VENV_PY or not GUNICORN:
        return jsonify({"error": "Virtualenv atau gunicorn tidak ditemukan."})

    # ---------------------------------------------
    # 2) STOP ALL BACKEND
    # ---------------------------------------------
    results["stop_gunicorn"] = stop_gunicorn()[1]
    results["stop_nginx"]    = stop_nginx()[1]
    results["stop_flask"]    = stop_flask_dev()[1]

    # ---------------------------------------------
    # 3) START NGINX
    # ---------------------------------------------
    s = os.system("sudo systemctl start nginx")
    results["nginx_start"] = "NGINX berjalan." if s == 0 else "Gagal start NGINX."

    # ---------------------------------------------
    # 4) START GUNICORN (DAEMON MODE)
    # ---------------------------------------------
    GUNICORN_CMD = (
        f"{VENV_PY} -m gunicorn "
        f"-w 3 --threads 3 -b 127.0.0.1:5000 "
        f"--daemon --pid /tmp/gunicorn.pid "
        f"--access-logfile /tmp/gunicorn_access.log "
        f"--error-logfile /tmp/gunicorn_error.log "
        f"{WSGI_TARGET}"
    )

    g = os.system(GUNICORN_CMD)
    results["gunicorn_start"] = "Gunicorn berjalan." if g == 0 else "Gagal start Gunicorn."

    return jsonify({
        "status": "restart_selesai",
        "detail": results
    })



# ======================================================
#  SHUTDOWN SERVER
# ======================================================

@tools.route("/shutdown")
def BMS_tools_shutdown():

    if not BMS_tools_is_root():
        return "Akses ditolak!"

    BMS_write_log("SERVER SHUTDOWN DIPANGGIL")

    results = {
        "gunicorn": stop_gunicorn()[1],
        "nginx": stop_nginx()[1],
        "flask_dev": stop_flask_dev()[1]
    }

    return jsonify({
        "status": "shutdown_performed",
        "detail": results
    })



# ======================================================
#  READ LOG
# ======================================================

@tools.route("/log")
def BMS_tools_get_log():
    if not os.path.exists(LOG_FILE):
        return ""
    with open(LOG_FILE, "r") as f:
        return f.read()



# ======================================================
#  CLEAR LOG
# ======================================================

@tools.route("/log/clear")
def BMS_tools_clear_log():
    open(LOG_FILE, "w").close()
    return "Log dibersihkan!"