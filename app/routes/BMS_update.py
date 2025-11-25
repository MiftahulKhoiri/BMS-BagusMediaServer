import os
import subprocess
from flask import (
    Blueprint, request, jsonify, session, render_template
)
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log, LOG_FILE

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
#   🌐 GUI Update Page
# ======================================================
@update.route("/update/gui")
def BMS_update_gui():
    check = BMS_update_required()
    if check:
        return check

    return render_template("BMS_update.html")


# ======================================================
#   🔄 Jalankan Update Git + Install
# ======================================================
@update.route("/update/run")
def BMS_tool_update():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Menjalankan UPDATE (git pull)", username)

    try:
        # INFO AWAL GIT
        git_fetch = subprocess.getoutput("git fetch")
        git_status = subprocess.getoutput("git status -uno")

        BMS_write_log(f"git status: {git_status}", username)

        # DETEKSI ADA UPDATE
        ada_update = "Your branch is behind" in git_status or "git pull" in git_status

        # Jika ada update → jalankan git pull
        if ada_update:
            git_result = subprocess.getoutput("git pull")
            BMS_write_log(f"git pull output: {git_result}", username)

            pip_result = subprocess.getoutput("pip install -r requirements.txt")
            BMS_write_log(f"pip install output: {pip_result}", username)

            return jsonify({
                "updated": True,
                "message": "Update berhasil! Perubahan telah diterapkan.",
                "git_output": git_result,
                "pip_output": pip_result,
                "notify": "UPDATE TERBARU TELAH DIINSTALL"
            })

        else:
            BMS_write_log("Tidak ada pembaruan tersedia.", username)
            return jsonify({
                "updated": False,
                "message": "Tidak ada pembaruan.",
                "notify": "SERVER SUDAH VERSI TERBARU"
            })

    except Exception as e:
        err_msg = f"Error update: {e}"
        BMS_write_log(err_msg, username)
        return jsonify({"error": str(e)})


# ======================================================
#   🔧 FUNGSI UPDATE SENDIRI (MANUAL)
#   → update tanpa git pull
# ======================================================
@update.route("/update/manual")
def BMS_tool_update_manual():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Menjalankan Update Manual (pip install)", username)

    try:
        pip_result = subprocess.getoutput("pip install -r requirements.txt")
        BMS_write_log(f"Pip manual install: {pip_result}", username)

        return jsonify({
            "status": "ok",
            "message": "Install/manual update selesai.",
            "pip_output": pip_result,
            "notify": "UPDATE MANUAL BERHASIL"
        })

    except Exception as e:
        BMS_write_log(f"Manual update error: {e}", username)
        return jsonify({"error": str(e)})



# ======================================================
#   🔁 Restart Server (Simulasi)
# ======================================================
@update.route("/restart")
def BMS_tool_restart():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Server RESTART diminta", username)

    return jsonify({"status": "ok", "message": "Restart (simulasi)"})


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

    if not os.path.exists(LOG_FILE):
        return jsonify({"log": ""})

    with open(LOG_FILE, "r") as f:
        content = f.read()

    return jsonify({"log": content})


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

    open(LOG_FILE, "w").close()
    return jsonify({"status": "cleared"})