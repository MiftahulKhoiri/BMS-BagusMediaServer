import os
import subprocess
import zipfile
import shutil
from flask import Blueprint, jsonify, session, render_template, current_app
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import BASE

update = Blueprint("update", __name__, url_prefix="/update")

# Path default (pastikan PROJECT_ROOT di config app)
# current_app.config["PROJECT_ROOT"] harus di-set di app.py
UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# --------- Helper: hak akses ----------
def BMS_update_required_simple():
    """
    Kembalikan True jika user boleh melakukan update (admin/root).
    Gunakan ini di WebSocket dan endpoint yang butuh autentikasi.
    """
    if not BMS_auth_is_login():
        return False
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return False
    return True


# --------- UI route ----------
@update.route("/ui")
def BMS_update_ui():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403
    return render_template("BMS_update.html")


# --------- Check update via git (HTTP API) ----------
@update.route("/check-update")
def check_update():
    """
    Cek apakah ada update upstream dengan git fetch + git status.
    Memerlukan config PROJECT_ROOT di app config.
    """
    try:
        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            return jsonify({"update_available": False, "error": "PROJECT_ROOT tidak disetting atau tidak ada"}), 500

        # git fetch
        subprocess.run(["git", "fetch"], cwd=base_dir, check=False)

        # git status -uno
        status = subprocess.run(
            ["git", "status", "-uno"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )

        update_available = "behind" in status.stdout.lower() or "behind" in status.stderr.lower()

        return jsonify({
            "update_available": update_available,
            "output": status.stdout + ("\n" + status.stderr if status.stderr else "")
        })

    except Exception as e:
        return jsonify({
            "update_available": False,
            "error": str(e)
        }), 500


# --------- WebSocket realtime update (register via register_ws) ----------
def register_ws(sock):
    """
    Daftarkan WebSocket route. Panggil register_ws(sock) di app.py setelah
    membuat Sock(app).
    Contoh di app.py:
        from app.routes.BMS_update import register_ws
        register_ws(sock)
    """

    @sock.route("/ws/update")
    def ws_update(ws):
        # Periksa auth dulu
        try:
            if not BMS_update_required_simple():
                try:
                    ws.send("[ERROR] Unauthorized: hanya admin/root yang boleh menjalankan update")
                except:
                    pass
                return
        except Exception:
            # Jika cek auth error, kirim pesan dan stop
            try:
                ws.send("[ERROR] Gagal memeriksa autentikasi")
            except:
                pass
            return

        # Ambil project root
        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            try:
                ws.send("[ERROR] PROJECT_ROOT tidak disetting di konfigurasi server")
            except:
                pass
            return

        def safe_send(txt):
            try:
                ws.send(txt)
            except:
                # jika socket tertutup, hentikan pengiriman tapi jangan raise
                pass

        safe_send("[INFO] Memulai proses git pull...\n")

        try:
            # jalankan git pull
            proc = subprocess.Popen(
                ["git", "pull", "--no-edit"],
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # baca stdout baris per baris dan kirim ke client
            for raw_line in proc.stdout:
                line = raw_line.rstrip("\n")
                if line:
                    safe_send(line)

            proc.wait()
            code = proc.returncode
            if code == 0:
                safe_send("[DONE] git pull selesai (exit 0)")
                # log
                try:
                    username = session.get("username")
                except Exception:
                    username = None
                BMS_write_log(f"Git pull sukses oleh {username}", username)
            else:
                safe_send(f"[ERROR] git pull exit code {code}")
                BMS_write_log(f"Git pull gagal exit {code}", session.get("username"))

        except Exception as e:
            safe_send(f"[ERROR] Exception saat menjalankan git pull: {e}")
            try:
                BMS_write_log(f"Exception saat git pull: {e}", session.get("username"))
            except:
                pass

        # Inform akhir
        safe_send("[END]")