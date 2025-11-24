import os
from flask import Blueprint, render_template, send_from_directory, jsonify
from app.routes.BMS_auth import (
    BMS_auth_is_login,
)

media_video = Blueprint("media_video", __name__, url_prefix="/video")

# Lokasi folder video server (ubah sesuai lokasi kamu)
VIDEO_FOLDER = "/storage/emulated/0/BMS/VIDEO"


# ======================================================
#   🔐 Proteksi akses video
# ======================================================
def BMS_video_required():
    """Hanya user login yang boleh akses Video Player."""
    if not BMS_auth_is_login():
        return "❌ Anda belum login!"
    return None


# ======================================================
#   🎬 Halaman Video Player
# ======================================================
@media_video.route("/player")
def BMS_video_player_page():
    check = BMS_video_required()
    if check:
        return check

    # memuat file HTML: BMS_video.html
    return render_template("BMS_video.html")


# ======================================================
#   🎬 API: Ambil daftar video
# ======================================================
@media_video.route("/list")
def BMS_video_list():
    check = BMS_video_required()
    if check:
        return check

    if not os.path.exists(VIDEO_FOLDER):
        return jsonify({"error": "Folder VIDEO tidak ditemukan!"})

    files = [
        f for f in os.listdir(VIDEO_FOLDER)
        if f.lower().endswith((".mp4", ".mkv", ".webm", ".avi"))
    ]

    return jsonify(files)


# ======================================================
#   🎬 API: Streaming file Video
# ======================================================
@media_video.route("/stream/<filename>")
def BMS_video_stream(filename):
    check = BMS_video_required()
    if check:
        return check

    return send_from_directory(VIDEO_FOLDER, filename)