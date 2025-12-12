import os
import signal
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from app.routes.BMS_auth.session_helpers import (
    BMS_auth_is_root,
    BMS_auth_is_admin
)

BMS_power = Blueprint("BMS_power", __name__, url_prefix="/power")

# ============================================================
#  PROTEKSI PENTING
# ============================================================
def require_power_access():
    """
    Hanya ROOT / ADMIN yang boleh mematikan server.
    """
    if not session.get("user_id"):
        return jsonify({"error": "Belum login!"}), 403

    role = session.get("role")
    if role not in ("root", "admin"):
        return jsonify({"error": "Akses ditolak! Perlu admin/root"}), 403

    return None


# ============================================================
#  SHUTDOWN (AMAN UNTUK TERMUX / LINUX)
# ============================================================
@BMS_power.route("/shutdown", methods=["POST"])
def shutdown_server():
    cek = require_power_access()
    if cek:
        return cek

    username = session.get("username", "UNKNOWN")
    BMS_write_log("Server diminta shutdown", username)

    # Coba hentikan Gunicorn jika ada
    pid_file = "/tmp/gunicorn.pid"

    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
            return jsonify({"status": "success", "message": "Gunicorn dimatikan."})
        except Exception as e:
            return jsonify({"error": f"Gagal mematikan Gunicorn: {e}"}), 500

    # Jika tidak pakai Gunicorn → matikan proses Flask
    os.kill(os.getpid(), signal.SIGTERM)

    return jsonify({"status": "success", "message": "Server Flask dihentikan."})


# ============================================================
#  RESTART (KHUSUS GUNICORN)
# ============================================================
@BMS_power.route("/restart", methods=["POST"])
def restart_server():
    cek = require_power_access()
    if cek:
        return cek

    username = session.get("username", "UNKNOWN")
    BMS_write_log("Server diminta restart", username)

    pid_file = "/tmp/gunicorn.pid"

    # Hanya bisa restart jika pakai Gunicorn
    if not os.path.exists(pid_file):
        return jsonify({
            "error": "Server tidak berjalan di Gunicorn. Restart manual diperlukan."
        }), 400

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # Matikan Gunicorn
        os.kill(pid, signal.SIGTERM)

        # Mulai ulang dengan perintah yang aman
        os.system(
            "gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 "
            "--daemon --pid /tmp/gunicorn.pid "
            "--access-logfile /tmp/gunicorn_access.log "
            "--error-logfile /tmp/gunicorn_error.log "
            "app:create_app()"
        )

        return jsonify({"status": "success", "message": "Server berhasil direstart."})

    except Exception as e:
        return jsonify({"error": f"Gagal restart: {e}"}), 500