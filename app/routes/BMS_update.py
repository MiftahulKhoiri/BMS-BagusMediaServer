import os
import subprocess
from flask import Blueprint, jsonify, session, render_template, current_app
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import BASE

update = Blueprint("update", __name__, url_prefix="/update")

# Path default
UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# ---------------------------------------------------------
#  Helper hak akses
# ---------------------------------------------------------
def BMS_update_required_simple():
    """Cek apakah user boleh update (admin atau root)."""
    if not BMS_auth_is_login():
        return False
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return False
    return True


# ---------------------------------------------------------
#  UI ROUTE
# ---------------------------------------------------------
@update.route("/ui")
def BMS_update_ui():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403
    return render_template("BMS_update.html")


# ---------------------------------------------------------
#  CEK UPDATE via HTTP
# ---------------------------------------------------------
@update.route("/check-update")
def check_update():
    try:
        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            return jsonify({
                "update_available": False,
                "error": "PROJECT_ROOT tidak disetting atau tidak ada"
            }), 500

        subprocess.run(["git", "fetch"], cwd=base_dir)

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
        }), 500


# ---------------------------------------------------------
#  RESET PERUBAHAN LOKAL SEBELUM PULL
# ---------------------------------------------------------
def safe_reset_before_pull(base_dir):
    """
    Buang semua perubahan lokal:
    - git restore .
    - git clean -fd
    """
    try:
        subprocess.run(["git", "restore", "."], cwd=base_dir, check=False)
        subprocess.run(["git", "clean", "-fd"], cwd=base_dir, check=False)
        return True, "Reset lokal selesai"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------
#  WEBSOCKET: PROSES UPDATE REALTIME
# ---------------------------------------------------------
def register_ws(sock):

    @sock.route("/ws/update")
    def ws_update(ws):

        # Auth
        if not BMS_update_required_simple():
            ws.send("[ERROR] Tidak punya izin update (admin/root saja)")
            return

        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            ws.send("[ERROR] PROJECT_ROOT tidak valid")
            return

        # ------------------- RESET LOKAL -------------------
        ok, msg = safe_reset_before_pull(base_dir)
        ws.send(f"[RESET] {msg}")
        if not ok:
            ws.send("[ERROR] Reset gagal, update dibatalkan")
            return

        ws.send("[INFO] Memulai git pull...\n")

        # ------------------- PROSES PULL -------------------
        try:
            proc = subprocess.Popen(
                ["git", "pull", "--no-edit"],
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for raw_line in proc.stdout:
                line = raw_line.strip()
                if line:
                    ws.send(line)

            proc.wait()
            code = proc.returncode

            username = session.get("username")

            if code == 0:
                ws.send("[DONE] git pull selesai (exit 0)")
                BMS_write_log(f"Git pull sukses oleh {username}", username)
            else:
                ws.send(f"[ERROR] git pull gagal (exit {code})")
                BMS_write_log(f"Git pull gagal exit {code}", username)

        except Exception as e:
            ws.send(f"[ERROR] Exception saat git pull: {e}")
            BMS_write_log(f"Exception git pull: {e}", session.get("username"))

        ws.send("[END]")