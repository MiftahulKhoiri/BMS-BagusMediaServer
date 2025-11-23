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
#  UPDATE SERVER  (git pull)
# =====================================

@tools.route("/update")
def BMS_tools_update():
    if not BMS_tools_is_root():
        return "Akses ditolak!"

    return BMS_tools_run("git pull")


# =====================================
#  INSTALL PACKAGE  (pip install)
# =====================================

@tools.route("/install", methods=["POST"])
def BMS_tools_install():
    if not BMS_tools_is_root():
        return "Akses ditolak!"

    package = request.form.get("package")

    if not package:
        return "Nama paket tidak ada!"

    return BMS_tools_run(f"pip install {package}")


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

@tools.route("/shutdown")
def BMS_tools_shutdown():
    if not BMS_tools_is_root():
        return "Akses ditolak!"

    BMS_tools_write_log("SERVER SHUTDOWN")
    os.system("shutdown now")  # hati-hati: aktif kalau di Linux server
    return "Shutdown server..."


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