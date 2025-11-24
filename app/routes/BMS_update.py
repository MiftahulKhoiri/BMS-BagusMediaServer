import os
import subprocess
from flask import Blueprint, request, jsonify, session
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

update = Blueprint("update", __name__, url_prefix="/tools")


# ======================================================
#   🔐 Proteksi Root + Admin
# ======================================================
def BMS_update_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses update ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403

    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        BMS_write_log("Akses update ditolak (tanpa izin)", session.get("username"))
        return jsonify({"error": "Akses ditolak!"}), 403
    
    return None


# ======================================================
#   🔄 Update Server (git pull)
# ======================================================
@update.route("/update")
def BMS_tool_update():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Menjalankan UPDATE (git pull)", username)

    try:
        # Jalankan git pull
        result = subprocess.getoutput("git pull")
        BMS_write_log(f"Hasil update: {result}", username)
        return jsonify({"status": "ok", "output": result})
    except Exception as e:
        BMS_write_log(f"Error update: {e}", username)
        return jsonify({"error": str(e)})


# ======================================================
#   📦 Install Package (pip install)
# ======================================================
@update.route("/install", methods=["POST"])
def BMS_tool_install():
    check = BMS_update_required()
    if check:
        return check

    pkg = request.form.get("package")
    username = session.get("username")

    if not pkg:
        return jsonify({"error": "Nama package kosong!"})

    BMS_write_log(f"Install package dimulai: {pkg}", username)

    try:
        result = subprocess.getoutput(f"pip install {pkg}")
        BMS_write_log(f"Hasil install {pkg}: {result}", username)
        return jsonify({"status": "ok", "output": result})
    except Exception as e:
        BMS_write_log(f"Error install {pkg}: {e}", username)
        return jsonify({"error": str(e)})


# ======================================================
#   🔁 Restart Server (simulasi)
# ======================================================
@update.route("/restart")
def BMS_tool_restart():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Server RESTART diminta", username)

    # Untuk keamanan, hanya simulasi
    return jsonify({"status": "ok", "message": "Restart (simulasi)"})


# ======================================================
#   ⛔ Shutdown Server
# ======================================================
@update.route("/shutdown")
def BMS_tool_shutdown():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Server SHUTDOWN diminta", username)

    return jsonify({"status": "ok", "message": "Shutdown (simulasi)"})


# ======================================================
#   📜 Ambil Log
# ======================================================
@update.route("/log")
def BMS_tool_read_log():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Admin load system log", username)

    try:
        with open("/storage/emulated/0/BMS/logs/system.log", "r") as f:
            content = f.read()
        return jsonify({"log": content})
    except:
        return jsonify({"log": ""})


# ======================================================
#   🧹 Clear Log
# ======================================================
@update.route("/log/clear")
def BMS_tool_clear_log():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Clear log diminta", username)

    open("/storage/emulated/0/BMS/logs/system.log", "w").close()
    return jsonify({"status": "cleared"})