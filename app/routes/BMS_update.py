import os
import shutil
import zipfile
import requests
from flask import Blueprint, jsonify, session, render_template

from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import BASE

update = Blueprint("update", __name__, url_prefix="/update")

# ======================================================
#   CONFIG REPO GITHUB
# ======================================================
GITHUB_REPO = "https://github.com/baguschoiri/BMS-BagusMediaServer/archive/refs/heads/main.zip"

UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# ======================================================
#   🔐 Proteksi Akses Update
# ======================================================
def BMS_update_required():
    """Hanya admin / root yang boleh update"""
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login!"}), 403

    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses update hanya untuk admin/root!"}), 403

    return None


# ======================================================
#   🖥 HALAMAN GUI UPDATE
# ======================================================
@update.route("/ui")
def BMS_update_ui():
    check = BMS_update_required()
    if check:
        return check

    return render_template("BMS_update.html")

# ============================================
# API : CEK UPDATE
# ============================================
@update.route("/check-update")
def check_update():
    """
    Cek apakah server tertinggal dari GitHub.
    - git fetch → ambil update
    - git status -uno → cek apakah "behind"
    """
    try:
        base_dir = current_app.config["PROJECT_ROOT"]

        # Ambil update terbaru dari remote
        subprocess.run(["git", "fetch"], cwd=base_dir)

        # Cek status branch
        status = subprocess.run(
            ["git", "status", "-uno"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )

        update_available = "behind" in status.stdout.lower()

        return jsonify({
            "update_available": update_available,
            "output": status.stdout
        })

    except Exception as e:
        return jsonify({
            "update_available": False,
            "error": str(e)
        })


# ============================================
# WEBSOCKET UPDATE REALTIME
# ============================================
def register_ws(sock):
    """
    Websocket tidak bisa masuk blueprint default,
    jadi kita daftar websocket manual di app.py.

    Cara pemanggilan di app.py:
        register_ws(sock)
    """

    @sock.route("/ws/update")
    def ws_update(ws):
        base_dir = current_app.config["PROJECT_ROOT"]

        # Fungsi aman untuk mengirim pesan
        def safe_send(msg):
            try:
                ws.send(msg)
            except:
                pass  # WebSocket tertutup → biarkan tanpa error

        safe_send("[INFO] Memulai update...\n")

        try:
            # Jalankan git pull
            process = subprocess.Popen(
                ["git", "pull"],
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Kirim output baris demi baris
            for line in process.stdout:
                safe_send(line.strip())

        except Exception as e:
            safe_send(f"[ERROR] {e}")

        safe_send("[DONE]")

# ======================================================
#   📄 LOG UPDATE
# ======================================================
@update.route("/logs")
def BMS_update_logs():
    try:
        log_file = os.path.join(BASE, "logs", "system.log")
        with open(log_file, "r") as f:
            data = f.read()
        return jsonify({"log": data})
    except:
        return jsonify({"log": ""})