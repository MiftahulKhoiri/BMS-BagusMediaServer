import os
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, send_from_directory, session, render_template, current_app
from werkzeug.utils import secure_filename
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import DB_PATH, VIDEO_FOLDER

media_video = Blueprint("media_video", __name__, url_prefix="/video")

os.makedirs(VIDEO_FOLDER, exist_ok=True)

# ======================================================
# DB helper
# ======================================================
def get_db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ======================================================
# Proteksi login
# ======================================================
def BMS_video_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses video ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    return None

# ======================================================
# File video valid
# ======================================================
VALID_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")
def is_video_file(name):
    return name.lower().endswith(VALID_EXT)

# ======================================================
# UI video
# ======================================================
@media_video.route("/")
def BMS_video_page():
    if not BMS_auth_is_login():
        return render_template("BMS_login.html", error="Silakan login terlebih dahulu!")

    BMS_write_log("Membuka halaman BMS_video.html", session.get("username"))
    return render_template("BMS_video.html")

# ======================================================
# SCAN DB — *Versi Folder Library* (Jellyfin Style)
# ======================================================
@media_video.route("/scan-db", methods=["POST", "GET"])
def scan_db():
    cek = BMS_video_required()
    if cek:
        return cek

    username = session.get("username")
    BMS_write_log("Memulai scan folder & video (Jellyfin Mode)", username)

    # Path utama untuk Android / fallback untuk Linux/Windows
    ROOT_SCAN = "/storage/emulated/0"
    if not os.path.exists(ROOT_SCAN):
        ROOT_SCAN = os.path.expanduser("~")

    conn = get_db_conn()
    cur = conn.cursor()

    imported_folders = []
    imported_videos = []

    for root, dirs, files in os.walk(ROOT_SCAN):
        # Ambil semua video dalam folder
        video_files = [f for f in files if is_video_file(f)]
        if not video_files:
            continue  # next folder

        folder_name = os.path.basename(root)
        folder_path = root

        # ----------- simpan folder ke DB ------------
        folder = cur.execute(
            "SELECT id FROM folders WHERE folder_path=?",
            (folder_path,)
        ).fetchone()

        if folder:
            folder_id = folder["id"]
        else:
            cur.execute(
                "INSERT INTO folders (folder_name, folder_path) VALUES (?, ?)",
                (folder_name, folder_path)
            )
            folder_id = cur.lastrowid
            imported_folders.append(folder_name)
            BMS_write_log(f"Folder baru ditemukan: {folder_name}", username)

        # ----------- simpan video ke DB ------------
        for f in video_files:
            full = os.path.join(root, f)

            exists = cur.execute(
                "SELECT id FROM videos WHERE filepath=?",
                (full,)
            ).fetchone()

            if exists:
                continue

            size = os.path.getsize(full)
            added_at = datetime.utcnow().isoformat()

            cur.execute("""
                INSERT INTO videos (filename, filepath, folder_id, size, added_at)
                VALUES (?, ?, ?, ?, ?)
            """, (f, full, folder_id, size, added_at))

            imported_videos.append(f"{folder_name}/{f}")
            BMS_write_log(f"Video terdaftar: {full}", username)

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": imported_folders,
        "videos_added": imported_videos,
        "message": f"{len(imported_folders)} folder & {len(imported_videos)} video baru ditambahkan."
    })

# ======================================================
# LIST FOLDER UNTUK UI
# ======================================================
@media_video.route("/folders")
def list_folders():
    conn = get_db_conn()
    rows = conn.execute("""
        SELECT folders.id, folders.folder_name, folders.folder_path,
        COUNT(videos.id) AS total_video
        FROM folders
        LEFT JOIN videos ON videos.folder_id = folders.id
        GROUP BY folders.id
        ORDER BY folders.folder_name ASC
    """).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

# ======================================================
# LIST VIDEO PER FOLDER
# ======================================================
@media_video.route("/folder/<int:folder_id>/videos")
def folder_videos(folder_id):
    conn = get_db_conn()
    rows = conn.execute("""
        SELECT id, filename, filepath, size, added_at
        FROM videos
        WHERE folder_id=?
        ORDER BY id DESC
    """, (folder_id,)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

# ======================================================
# PLAY VIDEO
# ======================================================
@media_video.route("/play/<int:video_id>")
def play_video(video_id):
    cek = BMS_video_required()
    if cek:
        return cek

    conn = get_db_conn()
    row = conn.execute("SELECT filepath FROM videos WHERE id=?", (video_id,)).fetchone()
    conn.close()

    if not row:
        return "Video tidak ditemukan", 404

    fp = row["filepath"]
    if not os.path.exists(fp):
        return "File fisik tidak ditemukan!", 404

    return send_file(fp)

# ======================================================
# DELETE VIDEO DARI LIBRARY (TIDAK MENGHAPUS FILE FISIK)
# ======================================================
@media_video.route("/delete/<int:video_id>", methods=["POST"])
def delete_video(video_id):
    cek = BMS_video_required()
    if cek:
        return cek

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM videos WHERE id=?", (video_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "message": "Video dihapus dari library"})