import os
from flask import Blueprint, jsonify, request, send_from_directory, session
from app.routes.BMS_auth import (
    BMS_auth_is_login,
)
from app.routes.BMS_logger import BMS_write_log

media_video = Blueprint("media_video", __name__, url_prefix="/video")

# Folder video
VIDEO_FOLDER = "/storage/emulated/0/BMS/VIDEO/"
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
#   🛡 Sanitasi nama file (anti path traversal)
# ======================================================
def sanitize_filename(filename):
    if not filename:
        return None

    # Karakter terlarang
    bad_chars = ["..", "/", "\\", "|", "&", ";", "$", "`", ">", "<", "$("]
    for bad in bad_chars:
        if bad in filename:
            return None

    # Hanya video tertentu
    valid_ext = (".mp4", ".mkv", ".webm", ".avi", ".mov")
    if not filename.lower().endswith(valid_ext):
        return None

    return filename


# ======================================================
#   🎬 List file video
# ======================================================
@media_video.route("/list")
def BMS_video_list():
    check = BMS_video_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Meminta daftar video", username)

    valid_ext = (".mp4", ".mkv", ".webm", ".avi", ".mov")

    files = [
        f for f in os.listdir(VIDEO_FOLDER)
        if f.lower().endswith(valid_ext)
    ]

    return jsonify({"files": files})


# ======================================================
#   ▶ Putar video
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
        BMS_write_log(f"Nama file video ilegal: {filename}", username)
        return "❌ File tidak valid!"

    filepath = os.path.join(VIDEO_FOLDER, safe_name)

    if not os.path.exists(filepath):
        BMS_write_log(f"File video tidak ditemukan: {safe_name}", username)
        return "❌ File tidak ditemukan!"

    BMS_write_log(f"Memutar video: {safe_name}", username)

    return send_from_directory(VIDEO_FOLDER, safe_name)