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
#   🎬 List file video
# ======================================================
@media_video.route("/list")
def BMS_video_list():
    check = BMS_video_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Meminta daftar video", username)

    video_ext = (".mp4", ".mkv", ".webm", ".avi", ".mov")

    files = []
    for fname in os.listdir(VIDEO_FOLDER):
        if fname.lower().endswith(video_ext):
            files.append(fname)

    return jsonify({"files": files})


# ======================================================
#   ▶ Putar video
# ======================================================
@media_video.route("/play")
def BMS_video_play():
    check = BMS_video_required()
    if check:
        return check

    file = request.args.get("file")
    username = session.get("username")

    if not file:
        return "❌ Parameter file kosong!"

    filepath = os.path.join(VIDEO_FOLDER, file)

    if not os.path.exists(filepath):
        BMS_write_log(f"File video tidak ditemukan: {file}", username)
        return "❌ File tidak ditemukan!"

    BMS_write_log(f"Memutar video: {file}", username)

    return send_from_directory(VIDEO_FOLDER, file)