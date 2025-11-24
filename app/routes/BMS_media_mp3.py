import os
from flask import Blueprint, jsonify, request, send_from_directory, session
from app.routes.BMS_auth import (
    BMS_auth_is_login,
)
from app.routes.BMS_logger import BMS_write_log

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")

# Folder MP3
MP3_FOLDER = "/storage/emulated/0/BMS/MP3/"
os.makedirs(MP3_FOLDER, exist_ok=True)


# ======================================================
#   🔐 Proteksi login
# ======================================================
def BMS_mp3_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses MP3 ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    return None


# ======================================================
#   🎵 List file MP3
# ======================================================
@media_mp3.route("/list")
def BMS_mp3_list():
    check = BMS_mp3_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Meminta daftar MP3", username)

    files = []
    for fname in os.listdir(MP3_FOLDER):
        if fname.lower().endswith(".mp3"):
            files.append(fname)

    return jsonify({"files": files})


# ======================================================
#   ▶ Memutar MP3 (stream file)
# ======================================================
@media_mp3.route("/play")
def BMS_mp3_play():
    check = BMS_mp3_required()
    if check:
        return check

    file = request.args.get("file")
    username = session.get("username")

    if not file:
        return "❌ Parameter file kosong!"

    filepath = os.path.join(MP3_FOLDER, file)

    if not os.path.exists(filepath):
        BMS_write_log(f"File MP3 tidak ditemukan: {file}", username)
        return "❌ File tidak ditemukan!"

    BMS_write_log(f"Memutar MP3: {file}", username)

    return send_from_directory(MP3_FOLDER, file)