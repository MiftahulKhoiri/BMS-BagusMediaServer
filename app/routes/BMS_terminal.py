import os
import subprocess
from flask import Blueprint, request, jsonify, session, render_template
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

terminal = Blueprint("terminal", __name__, url_prefix="/terminal")

# Batas kerja terminal
SAFE_ROOT = "/storage/emulated/0/BMS/"


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
#   🛡 Sanitasi CMD
# ======================================================
def sanitize_cmd(cmd: str):
    """Blokir command berbahaya"""

    BLOCKED_KEYWORDS = [
        "rm -rf", "rm -f", "rm -r", "reboot", "shutdown",
        "mv /", "chmod 777 /", "chown", "dd if", "mkfs",
        "su", "sudo", "mount", "umount", "killall",
        "/proc", "/system", "/vendor", "/dev", "/data",
        ">", "<", "|", "&&", "||", ";", "`", "$(", ")"
    ]

    LOWER = cmd.lower()

    for word in BLOCKED_KEYWORDS:
        if word in LOWER:
            return False

    return True


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

    cmd = request.form.get("cmd", "").strip()
    user = session.get("username")

    if not cmd:
        return jsonify({"output": "Perintah kosong."})

    # Log
    BMS_write_log(f"Terminal CMD: {cmd}", user)

    # Blokir CMD berbahaya
    if not sanitize_cmd(cmd):
        BMS_write_log(f"CMD DIBLOKIR: {cmd}", user)
        return jsonify({"output": "❌ PERINTAH DIBLOKIR DEMI KEAMANAN!"})

    # Paksa working directory tetap di SAFE_ROOT
    try:
        result = subprocess.getoutput(f"cd {SAFE_ROOT} && {cmd}")
        return jsonify({"output": result})
    except Exception as e:
        BMS_write_log(f"Error terminal: {e}", user)
        return jsonify({"output": f"Error: {e}"})