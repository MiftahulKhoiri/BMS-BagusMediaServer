import os
import signal
import subprocess
from flask import Blueprint, request, jsonify, session
from app.routes.BMS_logger import BMS_write_log

tools = Blueprint("tools", __name__, url_prefix="/tools")

LOG_FILE = "bms_tools.log"


# =====================================
#  FUNGSI PENDUKUNG
# =====================================

def BMS_tools_is_root():
    """Cek apakah user login sebagai ROOT"""
    return session.get("role") == "root"


def BMS_tools_write_log(message):
    """Simpan log ke file tools"""
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")


def BMS_tools_run(command):
    """Menjalankan perintah shell dan menyimpan log"""
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
#  RESTART SERVER (AKAN DI-UPGRADE)
# =====================================

@tools.route("/restart")
def BMS_tools_restart():
    if not BMS_tools_is_root():
        return "Akses ditolak!"

    BMS_tools_write_log("SERVER RESTARTED")
    return "Server restart (simulasi)"


# =====================================
#  STOP GUNICORN
# =====================================

def stop_gunicorn():
    """Hentikan Gunicorn jika PID file ditemukan."""
    pid_file = "/tmp/gunicorn.pid"

    if not os.path.exists(pid_file):
        return False, "Gunicorn tidak berjalan (pid file tidak ditemukan)."

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)  # soft shutdown
        return True, f"Gunicorn dimatikan (PID {pid})."

    except Exception as e:
        return False, f"Gagal menghentikan Gunicorn: {e}"


# =====================================
#  STOP NGINX
# =====================================

def stop_nginx():
    """Stop nginx jika tersedia."""
    code = os.system("sudo systemctl stop nginx")
    if code == 0:
        return True, "NGINX berhasil dihentikan."
    return False, "Gagal menghentikan NGINX."


# =====================================
#  STOP FLASK DEV SERVER
# =====================================

def stop_flask_dev():
    """Stop Flask dev server (hanya untuk debugging)."""
    try:
        func = request.environ.get("werkzeug.server.shutdown")
        if func:
            func()
            return True, "Flask dev server dimatikan."
        return False, "Flask dev server tidak aktif."
    except Exception as e:
        return False, f"Gagal menghentikan Flask dev server: {e}"


# =====================================
#  SHUTDOWN SERVER (WINNER FUNCTION)
# =====================================

@tools.route("/shutdown")
def BMS_tools_shutdown():

    # ROOT check
    if not BMS_tools_is_root():
        return "Akses ditolak!"

    BMS_tools_write_log("SERVER SHUTDOWN DIPANGGIL")

    results = {}

    # Stop Gunicorn
    ok, msg = stop_gunicorn()
    results["gunicorn"] = msg

    # Stop NGINX
    ok2, msg2 = stop_nginx()
    results["nginx"] = msg2

    # Stop Flask (optional)
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