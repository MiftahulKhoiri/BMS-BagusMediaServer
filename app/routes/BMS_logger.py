import os
from datetime import datetime
from threading import Lock
from flask import Blueprint, jsonify, request, session

from app.BMS_config import LOG_FOLDER, LOG_PATH

logger = Blueprint("logger", __name__, url_prefix="/logger")

# Pastikan folder log tersedia
os.makedirs(LOG_FOLDER, exist_ok=True)

# Path untuk error log
ERROR_LOG_PATH = os.path.join(LOG_FOLDER, "error.log")

# Lock supaya thread aman
_log_lock = Lock()

# Batas log (5MB)
MAX_LOG_SIZE = 5 * 1024 * 1024


# ======================================================
#   📝 UTILS — LOG NORMAL
# ======================================================
def BMS_write_log(text, username="SYSTEM"):
    """Menulis log umum dengan aman + rotasi ukuran."""
    return _write_to_file(LOG_PATH, text, username)


# ======================================================
#   🧨 UTILS — LOG ERROR (FILE TERPISAH)
# ======================================================
def BMS_write_error(text, username="SYSTEM"):
    """Menulis log error ke file error.log."""
    return _write_to_file(ERROR_LOG_PATH, f"ERROR: {text}", username)


# ======================================================
#   🔧 CORE WRITER (DIPAKAI LOG BIASA & ERROR)
# ======================================================
def _write_to_file(path, text, username):
    """
    Fungsi inti penulisan log (dipakai untuk log normal & log error).
    """
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{time_now}] [{username}] {text}"

    try:
        with _log_lock:

            # Rotasi log jika terlalu besar
            if os.path.exists(path) and os.path.getsize(path) > MAX_LOG_SIZE:
                open(path, "w").close()

            with open(path, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")

    except Exception as e:
        print(f"[WARN] Gagal menulis log ke {path}: {e}")

    return formatted


# ======================================================
#   🔐 PROTEKSI (KHUSUS ADMIN/ROOT)
# ======================================================
def BMS_log_required():
    if not session.get("user_id"):
        return jsonify({"error": "Belum login!"}), 403

    if session.get("role") not in ("admin", "root"):
        return jsonify({"error": "Akses khusus admin / root!"}), 403

    return None


# ======================================================
#   📄 READ LOG UTAMA
# ======================================================
@logger.route("/read")
def BMS_logger_read():
    check = BMS_log_required()
    if check:
        return check

    if not os.path.exists(LOG_PATH):
        return jsonify({"log": ""}), 200

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        BMS_write_error(f"Gagal membaca log utama: {e}")
        return jsonify({"error": "Gagal membaca log!"}), 500

    return jsonify({"log": content}), 200


# ======================================================
#   🔥 READ ERROR LOG
# ======================================================
@logger.route("/read_error")
def BMS_logger_read_error():
    check = BMS_log_required()
    if check:
        return check

    if not os.path.exists(ERROR_LOG_PATH):
        return jsonify({"log": ""}), 200

    try:
        with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return jsonify({"error": f"Gagal membaca error log: {e}"}), 500

    return jsonify({"log": content}), 200


# ======================================================
#   🧹 CLEAR BOTH LOG
# ======================================================
@logger.route("/clear", methods=["POST"])
def BMS_logger_clear():
    check = BMS_log_required()
    if check:
        return check

    try:
        with _log_lock:
            open(LOG_PATH, "w").close()
            open(ERROR_LOG_PATH, "w").close()

        return jsonify({"status": "cleared"}), 200

    except Exception as e:
        BMS_write_error(f"Gagal clear log: {e}")
        return jsonify({"error": "Gagal clear log"}), 500


# ======================================================
#   ✍ MANUAL WRITE LOG NORMAL
# ======================================================
@logger.route("/write", methods=["POST"])
def BMS_logger_manual():
    check = BMS_log_required()
    if check:
        return check

    text = request.form.get("msg", "")
    username = session.get("username", "UNKNOWN")

    if not text.strip():
        return jsonify({"error": "Pesan log kosong!"}), 400

    BMS_write_log(text, username)
    return jsonify({"status": "ok"}), 200


# ======================================================
#   🔎 FILTER LOG BERDASARKAN USER
# ======================================================
@logger.route("/filter")
def BMS_logger_filter_user():
    check = BMS_log_required()
    if check:
        return check

    username = request.args.get("user", "").strip()
    if not username:
        return jsonify({"error": "Parameter user kosong!"}), 400

    if not os.path.exists(LOG_PATH):
        return jsonify({"log": []}), 200

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Cari baris log yang mengandung user
        filtered = [line for line in lines if f"[{username}]" in line]

    except Exception as e:
        BMS_write_error(f"Gagal filter log user '{username}': {e}")
        return jsonify({"error": "Gagal filter log!"}), 500

    return jsonify({"log": filtered}), 200