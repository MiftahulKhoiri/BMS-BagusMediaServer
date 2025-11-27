import os
from flask import Blueprint, jsonify, request, send_file, session, render_template

# 🔗 Import config pusat (path sinkron)
from app.BMS_config import MP3_FOLDER, BASE
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")

# -----------------------------------------------
# 🔥 Folder resmi MP3 dari config
# -----------------------------------------------
BMS_MP3_FOLDER = MP3_FOLDER
os.makedirs(BMS_MP3_FOLDER, exist_ok=True)

# -----------------------------------------------
# 🔍 PATH pemindaian MP3 (kamu bisa tambah)
# -----------------------------------------------
SCAN_PATHS = [
    "/storage/emulated/0/Music",
    "/storage/emulated/0/Download",
    "/storage/emulated/0/WhatsApp/Media",
    "/storage/emulated/0/",
    BMS_MP3_FOLDER
]


# ======================================================
#   🔐 Proteksi login
# ======================================================
def BMS_mp3_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses MP3 ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    return None


# ======================================================
#   🛡 Sanitasi path MP3
# ======================================================
def sanitize_filename(path):
    if not path:
        return None

    # Anti hack
    bad = ["..", ";", "&", "|", "$", "`"]
    for b in bad:
        if b in path:
            return None

    # Wajib MP3
    if not path.lower().endswith(".mp3"):
        return None

    return path


# ======================================================
#   🔍 SCAN recursive MP3
# ======================================================
def scan_all_mp3():
    mp3_list = []

    for root_path in SCAN_PATHS:
        if not os.path.exists(root_path):
            continue

        for root, dirs, files in os.walk(root_path):
            for f in files:
                if f.lower().endswith(".mp3"):
                    full_path = os.path.join(root, f)
                    mp3_list.append(full_path)

    return mp3_list


# ======================================================
#   🎵 API: SCAN semua MP3
# ======================================================
@media_mp3.route("/scan")
def BMS_mp3_scan():
    check = BMS_mp3_required()
    if check:
        return check

    username = session.get("username")

    BMS_write_log("SCAN MP3 seluruh perangkat", username)

    mp3_files = scan_all_mp3()

    # Simpan di session
    session["mp3_list"] = mp3_files

    return jsonify({
        "total": len(mp3_files),
        "files": mp3_files
    })


# ======================================================
#   🎶 API: LIST MP3 (hasil scan)
# ======================================================
@media_mp3.route("/list")
def BMS_mp3_list():
    check = BMS_mp3_required()
    if check:
        return check

    mp3_files = session.get("mp3_list", [])

    return jsonify({
        "total": len(mp3_files),
        "files": mp3_files
    })


# ======================================================
#   ▶ PLAY FILE MP3
# ======================================================
@media_mp3.route("/play")
def BMS_mp3_play():
    check = BMS_mp3_required()
    if check:
        return check

    file_path = request.args.get("file")
    username = session.get("username")

    if not file_path:
        return "❌ Parameter file kosong!"

    safe = sanitize_filename(file_path)
    if not safe:
        BMS_write_log("Nama file ilegal", username)
        return "❌ File tidak valid!"

    if not os.path.exists(file_path):
        BMS_write_log(f"MP3 Hilang: {file_path}", username)
        return "❌ File tidak ditemukan!"

    BMS_write_log(f"Memutar MP3: {file_path}", username)
    return send_file(file_path)


# ======================================================
#   🎧 GUI MP3 PLAYER
# ======================================================
@media_mp3.route("/player")
def BMS_mp3_gui():
    check = BMS_mp3_required()
    if check:
        return check

    return render_template("BMS_mp3.html")