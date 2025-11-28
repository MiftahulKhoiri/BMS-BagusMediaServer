import os
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, send_from_directory, session, render_template, current_app
from werkzeug.utils import secure_filename
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log

# Import config
from app.BMS_config import DB_PATH, VIDEO_FOLDER

media_video = Blueprint("media_video", __name__, url_prefix="/video")

# Pastikan folder untuk video lokal tetap ada (opsional)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# ======================================================
# DB helper (untuk tabel videos)
# ======================================================
def get_db_conn():
    # koneksi ke DB_PATH (yang sudah dipakai project)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ======================================================
# Proteksi login sederhana
# ======================================================
def BMS_video_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses video ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    return None

# ======================================================
# Sanitasi ekstensi video
# ======================================================
VALID_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")

def is_video_file(name):
    return name and name.lower().endswith(VALID_EXT)

# ======================================================
# UI Route -> halaman library
# ======================================================
@media_video.route("/")
def BMS_video_page():
    if not BMS_auth_is_login():
        BMS_write_log("Akses halaman video ditolak (belum login)", "UNKNOWN")
        return render_template("BMS_login.html", error="Silakan login terlebih dahulu!")

    username = session.get("username")
    BMS_write_log("Membuka halaman BMS_video.html", username)
    return render_template("BMS_video.html")

# ======================================================
# API: Scan file video di ROOT_SCAN dan masukkan ke DB
# (Tidak menyalin file, hanya menambahkan record ke DB)
# ======================================================
@media_video.route("/scan-db", methods=["POST", "GET"])
def BMS_video_scan_db():
    check = BMS_video_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Memulai scan video ke DB", username)

    # ROOT_SCAN: sesuaikan untuk Termux/Android/PC
    # Termux Android: "/storage/emulated/0"
    # Default gunakan home sebagai fallback
    ROOT_SCAN = "/storage/emulated/0"
    if not os.path.exists(ROOT_SCAN):
        ROOT_SCAN = os.path.expanduser("~")

    imported = []
    conn = get_db_conn()
    cur = conn.cursor()

    for root, dirs, files in os.walk(ROOT_SCAN):
        # skip node_modules/.cache atau folder sistem jika mau (opsional)
        for f in files:
            if is_video_file(f):
                full_path = os.path.join(root, f)
                try:
                    # cek sudah terdaftar?
                    exists = cur.execute("SELECT 1 FROM videos WHERE filepath=?", (full_path,)).fetchone()
                    if exists:
                        continue

                    size = os.path.getsize(full_path)
                    added_at = datetime.utcnow().isoformat()

                    cur.execute(
                        "INSERT INTO videos (filename, filepath, size, added_at) VALUES (?, ?, ?, ?)",
                        (f, full_path, size, added_at)
                    )
                    imported.append(full_path)
                    BMS_write_log(f"Scan-DB register video: {full_path}", username)
                except Exception as e:
                    BMS_write_log(f"Error scan video {full_path}: {e}", username)
                    # lanjutkan
                    continue

    conn.commit()
    conn.close()

    if not imported:
        return jsonify({"status":"ok","message":"Tidak ada video baru ditemukan.","imported": []})

    return jsonify({"status":"ok","message":f"{len(imported)} video baru ditambahkan.","imported": imported})

# ======================================================
# API: ambil library (list) dari DB (untuk UI)
# ======================================================
@media_video.route("/library")
def BMS_video_library():
    check = BMS_video_required()
    if check:
        return check

    conn = get_db_conn()
    rows = conn.execute("SELECT id, filename, filepath, size, added_at FROM videos ORDER BY id DESC").fetchall()
    conn.close()

    videos = []
    for r in rows:
        videos.append({
            "id": r["id"],
            "filename": r["filename"],
            "filepath": r["filepath"],
            "size": r["size"],
            "added_at": r["added_at"]
        })
    return jsonify(videos)

# ======================================================
# Play video by id (mengirim file dari filepath di DB)
# ======================================================
@media_video.route("/play/<int:video_id>")
def BMS_video_play(video_id):
    check = BMS_video_required()
    if check:
        return check

    conn = get_db_conn()
    row = conn.execute("SELECT filepath, filename FROM videos WHERE id=?", (video_id,)).fetchone()
    conn.close()

    if not row:
        return "Video tidak ditemukan di library", 404

    fp = row["filepath"]
    if not os.path.exists(fp):
        # tandai missing? (opsional)
        return "File video tidak ditemukan (mungkin sudah dipindah/hapus)", 404

    # Gunakan send_file agar bisa stream (biarkan server menentukan mimetype)
    try:
        return send_file(fp)
    except Exception as e:
        current_app.logger.error(f"Error serve video {fp}: {e}")
        return "Gagal mengirim file", 500

# ======================================================
# Hapus record video dari library (tidak menghapus file fisik)
# ======================================================
@media_video.route("/delete/<int:video_id>", methods=["POST", "GET"])
def BMS_video_delete(video_id):
    cek = BMS_video_required()
    if cek:
        return cek

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT filepath FROM videos WHERE id=?", (video_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return jsonify({"status":"error","message":"Video tidak ditemukan"}), 404

    # hanya hapus record DB, tidak menghapus file fisik
    cur.execute("DELETE FROM videos WHERE id=?", (video_id,))
    conn.commit()
    conn.close()
    BMS_write_log(f"Video id {video_id} dihapus dari library oleh {session.get('username')}", session.get('username'))

    return jsonify({"status":"ok","message":"Video dihapus dari library"})

# ======================================================
# (Opsional) Thumbnail route - jika kamu membuat thumbnail file di folder thumbnails
# atau ingin membuat dynamic thumbnail nanti.
# Saat ini kita cek apakah ada thumbnail di VIDEO_FOLDER/thumbnails/<id>.jpg
# ======================================================
@media_video.route("/thumbnail/<int:video_id>")
def BMS_video_thumbnail(video_id):
    thumb_dir = os.path.join(VIDEO_FOLDER, "thumbnails")
    thumb_path = os.path.join(thumb_dir, f"{video_id}.jpg")
    if os.path.exists(thumb_path):
        return send_from_directory(thumb_dir, f"{video_id}.jpg")
    # fallback image
    return send_from_directory(os.path.join(current_app.root_path, "static", "img"), "default_cover.jpg")