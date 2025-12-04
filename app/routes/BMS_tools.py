import os
import signal
from flask import jsonify
from app.routes.BMS_auth import BMS_auth_is_root
from app.routes.BMS_logger import BMS_write_log
from flask import Blueprint, request, jsonify, session
import subprocess, os

tools = Blueprint("tools", __name__, url_prefix="/tools")

LOG_FILE = "bms_tools.log"


# =====================================
#  FUNGSI PENDUKUNG
# =====================================

def BMS_tools_is_root():
    """Cek apakah user login sebagai ROOT"""
    return session.get("role") == "root"


def BMS_tools_write_log(message):
    """Simpan log ke file"""
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")


def BMS_tools_run(command):
    """Menjalankan perintah shell"""
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        result = output.decode()
        BMS_tools_write_log(result)
        return result
    except subprocess.CalledProcessError as e:
        error_msg = e.output.decode()
        BMS_tools_write_log("ERROR: " + error_msg)
        return error_msg

# =====================================
#  RESTART SERVER
# =====================================

@tools.route("/restart")
def BMS_tools_restart():
    if not BMS_tools_is_root():
        return "Akses ditolak!"

    # Catatan: restart flask dev server hanya simulasi
    BMS_tools_write_log("SERVER RESTARTED")
    return "Server restart (simulasi)"


# =====================================
#  SHUTDOWN SERVER
# =====================================

def stop_gunicorn():
    """Hentikan Gunicorn jika PID file ditemukan."""
    pid_file = "/tmp/gunicorn.pid"

    if not os.path.exists(pid_file):
        return False, "Gunicorn tidak berjalan (pid file tidak ditemukan)."

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)  # sama seperti CTRL+C
        return True, f"Gunicorn dimatikan (PID {pid})."

    except Exception as e:
        return False, f"Gagal menghentikan Gunicorn: {e}"


def stop_nginx():
    """Stop nginx jika tersedia."""
    code = os.system("sudo systemctl stop nginx")
    if code == 0:
        return True, "NGINX berhasil dihentikan."
    return False, "Gagal menghentikan NGINX (mungkin tidak sedang aktif)."


def stop_flask_dev():
    """Stop Flask dev server (hanya untuk debugging mode)."""
    try:
        func = request.environ.get("werkzeug.server.shutdown")
        if func:
            func()
            return True, "Flask dev server dimatikan."
        return False, "Flask dev server tidak aktif."
    except Exception as e:
        return False, f"Gagal menghentikan Flask dev server: {e}"


# ==============================================================
#   ENDPOINT SHUTDOWN SERVER (FLEKSIBEL)
# ==============================================================

@tools.route("/shutdown")
def BMS_tools_shutdown():

    # 1) Cek apakah ROOT
    if not BMS_auth_is_root():
        return "Akses ditolak!"

    BMS_write_log("SERVER SHUTDOWN DIPANGGIL")

    results = {}

    # 2) Matikan Gunicorn
    ok, msg = stop_gunicorn()
    results["gunicorn"] = msg

    # 3) Matikan NGINX (jika ada)
    ok2, msg2 = stop_nginx()
    results["nginx"] = msg2

    # 4) Matikan Flask dev server (jika sedang dipakai)
    ok3, msg3 = stop_flask_dev()
    results["flask_dev"] = msg3

    return jsonify({
        "status": "shutdown_performed",
        "detail": results
    })


# =====================================
#  LOG PANEL (GET)
# =====================================

@tools.route("/log")
def BMS_tools_get_log():
    if not os.path.exists(LOG_FILE):
        return ""

    with open(LOG_FILE, "r") as f:
        return f.read()


# =====================================
#  CLEAR LOG
# =====================================

@tools.route("/log/clear")
def BMS_tools_clear_log():
    open(LOG_FILE, "w").close()
    return "Log dibersihkan!"