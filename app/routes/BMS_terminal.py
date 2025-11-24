import subprocess
from flask import Blueprint, request, jsonify, session, render_template
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

terminal = Blueprint("terminal", __name__, url_prefix="/terminal")


# ======================================================
#   🔐 Proteksi: Hanya Admin / Root
# ======================================================
def BMS_terminal_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses terminal ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    
    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        BMS_write_log("Akses terminal ditolak (tanpa izin)", session.get("username"))
        return jsonify({"error": "Akses ditolak!"}), 403

    return None


# ======================================================
#   🖥 Halaman Terminal (UI)
# ======================================================
@terminal.route("/ui")
def BMS_terminal_ui():
    check = BMS_terminal_required()
    if check:
        return check
    
    username = session.get("username")
    BMS_write_log("Akses halaman terminal", username)

    return render_template("BMS_terminal.html")


# ======================================================
#   💻 Eksekusi Perintah Terminal
# ======================================================
@terminal.route("/run", methods=["POST"])
def BMS_terminal_run():
    check = BMS_terminal_required()
    if check:
        return check

    cmd = request.form.get("cmd", "")
    user = session.get("username")

    if not cmd:
        return jsonify({"output": "Perintah kosong."})

    # Catat command ke log
    BMS_write_log(f"Terminal CMD: {cmd}", user)

    # Blokir perintah berbahaya
    BLOCKED = ["rm -rf /", "shutdown", "reboot"]
    for bad in BLOCKED:
        if bad in cmd.lower():
            BMS_write_log(f"CMD DIBLOKIR: {cmd}", user)
            return jsonify({"output": "❌ PERINTAH DIBLOKIR DEMI KEAMANAN!"})

    try:
        # Jalankan command
        result = subprocess.getoutput(cmd)
        return jsonify({"output": result})
    except Exception as e:
        BMS_write_log(f"Error terminal: {e}", user)
        return jsonify({"output": f"Error: {e}"})