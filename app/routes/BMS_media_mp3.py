import os
from flask import Blueprint, render_template, send_from_directory, jsonify
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")

# Folder MP3 (silakan sesuaikan dengan lokasi kamu)
MP3_FOLDER = "/storage/emulated/0/BMS/MP3"


# ======================================================
#   🔐 Proteksi akses MP3 Player
# ======================================================
def BMS_mp3_required():
    """Hanya user login yang boleh akses MP3 Player."""
    if not BMS_auth_is_login():
        return "❌ Anda belum login!"
    return None


# ======================================================
#   🎵 Halaman MP3 Player
# ======================================================
@media_mp3.route("/player")
def BMS_mp3_player_page():
    check = BMS_mp3_required()
    if check:
        return check

    # load file HTML: BMS_mp3.html
    return render_template("BMS_mp3.html")


# ======================================================
#   🎵 API: Ambil daftar file MP3
# ======================================================
@media_mp3.route("/list")
def BMS_mp3_list():
    check = BMS_mp3_required()
    if check:
        return check

    if not os.path.exists(MP3_FOLDER):
        return jsonify({"error": "Folder MP3 tidak ditemukan!"})

    files = [
        f for f in os.listdir(MP3_FOLDER)
        if f.lower().endswith(".mp3")
    ]

    return jsonify(files)


# ======================================================
#   🎵 API: Streaming file MP3
# ======================================================
@media_mp3.route("/stream/<filename>")
def BMS_mp3_stream(filename):
    check = BMS_mp3_required()
    if check:
        return check

    return send_from_directory(MP3_FOLDER, filename)