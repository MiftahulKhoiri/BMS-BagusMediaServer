import os
from datetime import datetime
from flask import Blueprint, jsonify, request, session

# 🔗 Ambil path resmi dari Config
from app.BMS_config import LOG_FOLDER, LOG_PATH

logger = Blueprint("logger", __name__, url_prefix="/logger")

# Pastikan folder log benar-benar ada
os.makedirs(LOG_FOLDER, exist_ok=True)


# ======================================================
#   📝 Fungsi internal untuk modul lain (tanpa circular)
# ======================================================
def BMS_write_log(text, username="SYSTEM"):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{time_now}] [{username}] {text}"

    try:
        with open(LOG_PATH, "a") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"[WARN] Tidak bisa menulis log: {e}")

    return formatted


# ======================================================
#   🔐 Proteksi admin
#   tanpa import BMS_auth supaya tidak circular
# ======================================================
def BMS_log_required():
    if not session.get("user_id"):
        return jsonify({"error": "Belum login!"}), 403

    role = session.get("role", "user")
    if role not in ("admin", "root"):
        return jsonify({"error": "Hanya admin/root yang boleh!"}), 403

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
        return jsonify({"log": ""})

    with open(LOG_PATH, "r") as f:
        content = f.read()

    return jsonify({"log": content})


# ======================================================
#   🧹 CLEAR LOG
# ======================================================
@logger.route("/clear")
def BMS_logger_clear():
    check = BMS_log_required()
    if check:
        return check

    try:
        open(LOG_PATH, "w").close()
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": f"Gagal clear log: {e}"})


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
        return jsonify({"error": "msg kosong!"})

    BMS_write_log(text, username)
    return jsonify({"status": "ok"})