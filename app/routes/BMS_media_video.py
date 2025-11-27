import os
from flask import Blueprint, jsonify, request, send_from_directory, session
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log

# 🔗 Path sinkron dari Config
from app.BMS_config import VIDEO_FOLDER

media_video = Blueprint("media_video", __name__, url_prefix="/video")

# Pastikan folder video ada
os.makedirs(VIDEO_FOLDER, exist_ok=True)


# ======================================================
#   🔐 Proteksi login
# ======================================================
def BMS_video_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses video ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    return None


# ======================================================
#   🛡 Sanitasi nama file (anti hack traversal)
# ======================================================
def sanitize_filename(filename):
    if not filename:
        return None

    # karakter berbahaya / traversal
    bad_chars = ["..", "/", "\\", "|", "&", ";", "$", "`", ">", "<", "$("]
    for b in bad_chars:
        if b in filename:
            return None

    # format video yang diizinkan
    valid_ext = (".mp4", ".mkv", ".webm", ".avi", ".mov")
    if not filename.lower().endswith(valid_ext):
        return None

    return filename


# ======================================================
#   🎬 LIST VIDEO
# ======================================================
@media_video.route("/list")
def BMS_video_list():
    check = BMS_video_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Meminta daftar video", username)

    valid_ext = (".mp4", ".mkv", ".webm", ".avi", ".mov")

    try:
        files = [
            f for f in os.listdir(VIDEO_FOLDER)
            if f.lower().endswith(valid_ext)
        ]
    except Exception as e:
        BMS_write_log(f"Error membaca folder video: {e}", username)
        return jsonify({"error": "Folder video tidak dapat dibaca!"}), 500

    return jsonify({"files": files})


# ======================================================
#   ▶ PUTAR VIDEO
# ======================================================
@media_video.route("/play")
def BMS_video_play():
    check = BMS_video_required()
    if check:
        return check

    filename = request.args.get("file")
    username = session.get("username")

    safe_name = sanitize_filename(filename)
    if not safe_name:
        BMS_write_log(f"Nama file ilegal: {filename}", username)
        return "❌ Nama file tidak valid!"

    target = os.path.join(VIDEO_FOLDER, safe_name)

    if not os.path.exists(target):
        BMS_write_log(f"Video tidak ditemukan: {safe_name}", username)
        return "❌ File tidak ditemukan!"

    BMS_write_log(f"Memutar video: {safe_name}", username)

    # Kakak: gunakan send_from_directory agar aman
    return send_from_directory(VIDEO_FOLDER, safe_name)