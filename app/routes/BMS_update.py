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
#   🔄 Update Server (git pull + auto install requirements)
# ======================================================
@update.route("/update/run")
def BMS_tool_update():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Menjalankan UPDATE (git pull)", username)

    try:
        # Jalankan git pull
        git_result = subprocess.getoutput("git pull")
        BMS_write_log(f"Hasil git pull: {git_result}", username)

        # Cek apakah ada perubahan
        updated = (
            "Updating" in git_result
            or "Fast-forward" in git_result
            or "changed" in git_result
        )

        pip_result = ""

        # Jika ada perubahan → jalankan install
        if updated:
            BMS_write_log("Perubahan terdeteksi. Menjalankan install dependensi...", username)
            pip_result = subprocess.getoutput("pip install -r requirements.txt")
            BMS_write_log(f"Hasil install requirements: {pip_result}", username)
        else:
            pip_result = "Tidak ada perubahan. Install dilewati."
            BMS_write_log(pip_result, username)

        return jsonify({
            "status": "ok",
            "git_output": git_result,
            "install_output": pip_result
        })

    except Exception as e:
        BMS_write_log(f"Error update: {e}", username)
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