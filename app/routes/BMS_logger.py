import os
from datetime import datetime
from threading import Lock
from flask import Blueprint, jsonify, request, session

from app.BMS_config import LOG_FOLDER, LOG_PATH

logger = Blueprint("logger", __name__, url_prefix="/logger")

# Pastikan folder log ada
os.makedirs(LOG_FOLDER, exist_ok=True)

# Lock untuk mencegah race condition
_log_lock = Lock()

# Maksimal ukuran log (opsional, 5MB)
MAX_LOG_SIZE = 5 * 1024 * 1024


# ======================================================
#   📝 Fungsi internal untuk modul lain
# ======================================================
def BMS_write_log(text, username="SYSTEM"):
    """
    Menulis log secara aman (thread-safe)
    """
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{time_now}] [{username}] {text}"

    try:
        with _log_lock:

            # Jika file terlalu besar → auto clear
            if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > MAX_LOG_SIZE:
                open(LOG_PATH, "w").close()

            with open(LOG_PATH, "a") as f:
                f.write(formatted + "\n")

    except Exception as e:
        print(f"[WARN] Tidak bisa menulis log: {e}")

    return formatted


# ======================================================
#   🔐 Middleware proteksi admin / root
# ======================================================
def BMS_log_required():
    if not session.get("user_id"):
        return jsonify({"error": "Belum login!"}), 403

    role = session.get("role", "user")
    if role not in ("admin", "root"):
        return jsonify({"error": "Akses khusus admin / root!"}), 403

    return None


# ======================================================
#   📄 READ LOG
# ======================================================
@logger.route("/read")
def BMS_logger_read():
    check = BMS_log_required()
    if check:
        return check

    if not os.path.exists(LOG_PATH):
        return jsonify({"log": ""}), 200

    try:
        with open(LOG_PATH, "r") as f:
            content = f.read()
    except Exception as e:
        return jsonify({"error": f"Gagal membaca log: {e}"}), 500

    return jsonify({"log": content}), 200


# ======================================================
#   🧹 CLEAR LOG
# ======================================================
@logger.route("/clear", methods=["POST"])
def BMS_logger_clear():
    check = BMS_log_required()
    if check:
        return check

    try:
        with _log_lock:
            open(LOG_PATH, "w").close()
        return jsonify({"status": "cleared"}), 200

    except Exception as e:
        return jsonify({"error": f"Gagal clear log: {e}"}), 500


# ======================================================
#   ✍ WRITE LOG MANUAL
# ======================================================
@logger.route("/write", methods=["POST"])
def BMS_logger_manual():
    check = BMS_log_required()
    if check:
        return check

    text = request.form.get("msg", "")
    username = session.get("username", "UNKNOWN")

    if not text:
        return jsonify({"error": "Pesan log kosong!"}), 400

    BMS_write_log(text, username)
    return jsonify({"status": "ok"}), 200