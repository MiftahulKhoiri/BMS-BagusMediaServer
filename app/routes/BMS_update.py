import os
import subprocess
from flask import Blueprint, request, jsonify
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

update = Blueprint("update", __name__, url_prefix="/tools")

# Folder untuk menyimpan log update
LOG_FILE = "/storage/emulated/0/BMS/update.log"


# ======================================================
#   🔐 Proteksi akses (hanya ROOT/ADMIN boleh update)
# ======================================================
def BMS_update_required():
    if not BMS_auth_is_login():
        return "❌ Anda belum login!"

    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return "❌ Hanya ROOT atau ADMIN yang dapat melakukan update!"

    return None


# ======================================================
#   📝 Fungsi mencatat log
# ======================================================
def write_log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")


# ======================================================
#   🔄 Git Pull (Update Server)
# ======================================================
@update.route("/update")
def BMS_update_git():
    check = BMS_update_required()
    if check:
        return check

    try:
        result = subprocess.getoutput("git pull")
        write_log("=== GIT UPDATE ===")
        write_log(result)
        return "✔ Update selesai!"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


# ======================================================
#   📦 Install Package (pip install)
# ======================================================
@update.route("/install", methods=["POST"])
def BMS_update_install_pkg():
    check = BMS_update_required()
    if check:
        return check

    pkg = request.form.get("package")

    if not pkg:
        return "❌ Nama package kosong!"

    try:
        result = subprocess.getoutput(f"pip install {pkg}")
        write_log(f"=== INSTALL PACKAGE: {pkg} ===")
        write_log(result)
        return f"✔ Install selesai: {pkg}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


# ======================================================
#   🔁 Restart Server (Simulasi)
# ======================================================
@update.route("/restart")
def BMS_update_restart():
    check = BMS_update_required()
    if check:
        return check

    write_log("=== SERVER RESTART (SIMULATION) ===")
    return "✔ Server restart (simulasi)!"


# ======================================================
#   ⛔ Shutdown Server (Simulasi)
# ======================================================
@update.route("/shutdown")
def BMS_update_shutdown():
    check = BMS_update_required()
    if check:
        return check

    write_log("=== SERVER SHUTDOWN (SIMULATION) ===")
    return "✔ Server shutdown (simulasi)!"


# ======================================================
#   📄 Ambil Log
# ======================================================
@update.route("/log")
def BMS_update_log():
    check = BMS_update_required()
    if check:
        return check

    if not os.path.exists(LOG_FILE):
        return "Log kosong."

    with open(LOG_FILE, "r") as f:
        return f.read()


# ======================================================
#   🧹 Hapus Log
# ======================================================
@update.route("/log/clear")
def BMS_update_log_clear():
    check = BMS_update_required()
    if check:
        return check

    open(LOG_FILE, "w").close()
    return "✔ Log dibersihkan!"