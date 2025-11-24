import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

logger = Blueprint("logger", __name__, url_prefix="/logger")

LOG_FILE = "/storage/emulated/0/BMS/logs/system.log"

# pastikan folder log ada
os.makedirs("/storage/emulated/0/BMS/logs", exist_ok=True)


# ======================================================
#   📌 Fungsi internal untuk modul lain
# ======================================================
def BMS_write_log(text, username="SYSTEM"):

    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{time_now}] [{username}] {text}"

    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")

    return formatted


# ======================================================
#   🔐 Proteksi admin
# ======================================================
def BMS_log_required():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login!"}), 403
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Hanya admin/root!"}), 403
    return None


# ======================================================
#   📄 Ambil log
# ======================================================
@logger.route("/read")
def BMS_logger_read():
    check = BMS_log_required()
    if check:
        return check

    if not os.path.exists(LOG_FILE):
        return jsonify({"log": ""})

    with open(LOG_FILE, "r") as f:
        content = f.read()

    return jsonify({"log": content})


# ======================================================
#   🧹 Clear log
# ======================================================
@logger.route("/clear")
def BMS_logger_clear():
    check = BMS_log_required()
    if check:
        return check

    open(LOG_FILE, "w").close()
    return jsonify({"status": "cleared"})


# ======================================================
#   📝 Endpoint manual write
# ======================================================
@logger.route("/write", methods=["POST"])
def BMS_logger_manual():
    check = BMS_log_required()
    if check:
        return check

    text = request.form.get("msg", "")
    username = request.form.get("user", "UNKNOWN")

    BMS_write_log(text, username)
    return jsonify({"status": "ok"})