import os
import subprocess
from flask import Blueprint, request, jsonify, session, render_template

# 🔗 Import konfigurasi path
from app.BMS_config import BASE

from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

terminal = Blueprint("terminal", __name__, url_prefix="/terminal")

# ======================================================
#   🔒 BATAS KERJA TERMINAL (sesuai Config)
# ======================================================
SAFE_ROOT = BASE               # FULL sinkron
os.makedirs(SAFE_ROOT, exist_ok=True)


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
#   🛡 Sanitasi CMD (blokir perintah berbahaya)
# ======================================================
def sanitize_cmd(cmd: str):
    BLOCKED_KEYWORDS = [
        "rm -rf", "rm -f", "rm -r",
        "reboot", "shutdown",
        "mv /", "chmod 777 /", "chown", "dd if", "mkfs",
        "su", "sudo", "mount", "umount",
        "killall", "/proc", "/system", "/vendor", "/dev", "/data",
        ">", "<", "|", "&&", "||", ";", "`", "$(", ")"
    ]

    c = cmd.lower()
    for word in BLOCKED_KEYWORDS:
        if word in c:
            return False

    return True


# ======================================================
#   🖥 Halaman Terminal UI
# ======================================================
@terminal.route("/ui")
def BMS_terminal_ui():
    check = BMS_terminal_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Buka halaman terminal", username)

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
    username = session.get("username")

    if not cmd:
        return jsonify({"output": "Perintah kosong."})

    # Catat log
    BMS_write_log(f"CMD: {cmd}", username)

    # Blokir perintah berbahaya
    if not sanitize_cmd(cmd):
        BMS_write_log(f"CMD diblokir: {cmd}", username)
        return jsonify({"output": "❌ PERINTAH DIBLOKIR DEMI KEAMANAN!"})

    # Eksekusi aman di direktori BASE
    try:
        result = subprocess.getoutput(f"cd {SAFE_ROOT} && {cmd}")
        return jsonify({"output": result})
    except Exception as e:
        BMS_write_log(f"Terminal error: {e}", username)
        return jsonify({"output": f"Error: {e}"})