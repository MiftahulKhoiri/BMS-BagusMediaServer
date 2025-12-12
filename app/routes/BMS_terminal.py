import os
import subprocess
import shlex
import re
from flask import Blueprint, request, jsonify, session, render_template

from app.BMS_config import BASE
from app.routes.BMS_auth.session_helpers import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

terminal = Blueprint("terminal", __name__, url_prefix="/terminal")

SAFE_ROOT = os.path.realpath(BASE)
os.makedirs(SAFE_ROOT, exist_ok=True)


# ======================================================
# 🔐 Proteksi akses terminal
# ======================================================
def BMS_terminal_required():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login!"}), 403
    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return jsonify({"error": "Akses ditolak!"}), 403
    return None


# ======================================================
# 🛡 Sanitasi perintah: HARD MODE
# ======================================================
BLOCKED_REGEX = re.compile(
    r"(rm\s+-rf|rm\s+-r|reboot|shutdown|halt|mkfs|mount|umount|"
    r"dd\s+if|sudo|su|killall|systemctl|chmod\s+777|chown|"
    r"mv\s+/|:>|;|&&|\|\||>|<|\$|`|\(|\))",
    re.IGNORECASE
)

WHITELIST_SAFE_COMMANDS = [
    "ls", "cd", "pwd", "cat", "echo", "whoami", "id", "du", "df",
    "top", "uname", "lsblk", "date", "uptime", "ps", "free",
]

def sanitize_cmd(cmd):
    # Normalisasi input
    raw = cmd.strip().lower()

    # Blokir berdasarkan regex
    if BLOCKED_REGEX.search(raw):
        return False

    # Blokir command yang mencoba keluar root
    if "../" in raw or raw.startswith("/") and not raw.startswith(SAFE_ROOT):
        return False

    # Optional safety mode: command wajib di whitelist
    head = raw.split(" ")[0]
    if head not in WHITELIST_SAFE_COMMANDS:
        return False

    return True


# ======================================================
# UI Terminal
# ======================================================
@terminal.route("/ui")
def terminal_ui():
    cek = BMS_terminal_required()
    if cek:
        return cek

    BMS_write_log("Membuka halaman terminal", session.get("username"))
    return render_template("BMS_terminal.html")


# ======================================================
# EKSEKUSI PERINTAH SAFE MODE (tanpa shell injection)
# ======================================================
@terminal.route("/run", methods=["POST"])
def BMS_terminal_run():
    cek = BMS_terminal_required()
    if cek:
        return cek

    cmd = request.form.get("cmd", "").strip()
    username = session.get("username")

    if not cmd:
        return jsonify({"output": "Perintah kosong."})

    # Log perintah
    BMS_write_log(f"CMD: {cmd}", username)

    # Sanitasi
    if not sanitize_cmd(cmd):
        BMS_write_log(f"CMD diblokir: {cmd}", username)
        return jsonify({"output": "❌ Perintah diblokir oleh sistem keamanan!"})

    try:
        # Ubah command menjadi list agar TIDAK ada injection
        parts = shlex.split(cmd)

        # Jalankan dalam BASE ROOT
        process = subprocess.Popen(
            parts,
            cwd=SAFE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=5)

        output = (stdout + stderr).strip()

        # Batas maksimal output 5000 karakter
        if len(output) > 5000:
            output = output[:5000] + "\n\n[Output dipotong karena terlalu panjang]"

        return jsonify({"output": output})

    except subprocess.TimeoutExpired:
        return jsonify({"output": "⚠️ Perintah berjalan terlalu lama (timeout)."})
    except Exception as e:
        BMS_write_log(f"Terminal Error: {e}", username)
        return jsonify({"output": f"Error: {e}"}), 500