import os
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, Response, session, render_template
from werkzeug.utils import secure_filename

from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import DB_PATH, VIDEO_FOLDER

media_video = Blueprint("media_video", __name__, url_prefix="/video")

# Pastikan folder video ada
os.makedirs(VIDEO_FOLDER, exist_ok=True)


# ============================================================================
#  DB HELPER + AUTO INIT TABLE
# ============================================================================
_db_initialized = False
def get_db_conn():
    global _db_initialized

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT,
                folder_path TEXT UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT UNIQUE,
                folder_id INTEGER,
                size INTEGER,
                added_at TEXT,
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        _db_initialized = True

    return conn


# ============================================================================
#  Proteksi login
# ============================================================================
def BMS_video_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses video ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Belum login!"}), 403
    return None


# ============================================================================
#  Validasi file video
# ============================================================================
VALID_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")
def is_video_file(name):
    return isinstance(name, str) and name.lower().endswith(VALID_EXT)


# ============================================================================
#  Aman-kan path (tidak boleh keluar dari root folder)
# ============================================================================
def is_inside_video_folder(path):
    try:
        real = os.path.realpath(path)
        base = os.path.realpath(VIDEO_FOLDER)
        return real.startswith(base)
    except:
        return False


# ============================================================================
#  HALAMAN UTAMA VIDEO
# ============================================================================
@media_video.route("/")
def BMS_video_page():
    if not BMS_auth_is_login():
        return render_template("BMS_login.html", error="Silakan login dahulu!")

    BMS_write_log("Membuka halaman BMS_video.html", session.get("username"))
    return render_template("BMS_video.html")


# ============================================================================
#  SCAN STORAGE → DIBATASI AGAR TIDAK MEMBEKU
# ============================================================================
@media_video.route("/scan-db", methods=["POST", "GET"])
def scan_db():
    cek = BMS_video_required()
    if cek:
        return cek

    username = session.get("username")

    BMS_write_log("Memulai scan video mode library", username)

    ROOT_SCAN = "/storage/emulated/0"
    if not os.path.exists(ROOT_SCAN):
        ROOT_SCAN = os.path.expanduser("~")

    MAX_FOLDERS = 200
    MAX_FILES_PER_FOLDER = 300

    conn = get_db_conn()
    cur = conn.cursor()

    imported_folders = []
    imported_videos = []

    count_folders = 0

    for root, dirs, files in os.walk(ROOT_SCAN):
        if count_folders >= MAX_FOLDERS:
            break

        videos = [f for f in files if is_video_file(f)]
        if not videos:
            continue

        # batasi jumlah folder agar tidak hang
        count_folders += 1

        folder_name = os.path.basename(root)
        folder_path = root

        # Simpan folder
        folder = cur.execute(
            "SELECT id FROM folders WHERE folder_path=?",
            (folder_path,)
        ).fetchone()

        if folder:
            folder_id = folder["id"]
        else:
            cur.execute(
                "INSERT INTO folders (folder_name, folder_path) VALUES (?,?)",
                (folder_name, folder_path)
            )
            folder_id = cur.lastrowid
            imported_folders.append(folder_name)
            BMS_write_log(f"Folder baru: {folder_name}", username)

        # Simpan video (dengan limit per folder)
        for v in videos[:MAX_FILES_PER_FOLDER]:
            fp = os.path.join(root, v)

            if not os.path.exists(fp):
                continue

            exists = cur.execute(
                "SELECT id FROM videos WHERE filepath=?", (fp,)
            ).fetchone()
            if exists:
                continue

            size = os.path.getsize(fp)
            added_at = datetime.utcnow().isoformat()

            cur.execute("""
                INSERT INTO videos (filename, filepath, folder_id, size, added_at)
                VALUES (?, ?, ?, ?, ?)
            """, (v, fp, folder_id, size, added_at))

            imported_videos.append(f"{folder_name}/{v}")
            BMS_write_log(f"Video terdaftar: {fp}", username)

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": imported_folders,
        "videos_added": imported_videos,
        "message": f"{len(imported_folders)} folder & {len(imported_videos)} video baru."
    })


# ============================================================================
#  LIST FOLDERS
# ============================================================================
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


# ============================================================================
#  LIST VIDEO DALAM FOLDER
# ============================================================================
@media_video.route("/folder/<int:folder_id>/videos")
def folder_videos(folder_id):
    conn = get_db_conn()
    rows = conn.execute("""
        SELECT id, filename, filepath, size, added_at
        FROM videos
        WHERE folder_id=?
        ORDER BY filename ASC
    """, (folder_id,)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ============================================================================
#  STREAM VIDEO (FULL HEADER RANGE SUPPORT)
# ============================================================================
def parse_range_header(path):
    range_header = request.headers.get('Range')
    if not range_header:
        return None

    try:
        size = os.path.getsize(path)
        bytes_unit, range_spec = range_header.split("=")
        start_str, end_str = range_spec.split("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else size - 1

        if end >= size:
            end = size - 1

        return start, end, size
    except:
        return None


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
        return "File tidak ditemukan", 404

    if not is_inside_video_folder(fp):
        return jsonify({"error": "Akses path tidak diizinkan"}), 403

    range_info = parse_range_header(fp)

    if range_info:
        start, end, size = range_info
        chunk_size = end - start + 1

        with open(fp, "rb") as f:
            f.seek(start)
            data = f.read(chunk_size)

        resp = Response(data, 206, mimetype="video/mp4", direct_passthrough=True)
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(chunk_size))
        return resp

    return Response(open(fp, "rb").read(), mimetype="video/mp4")


# ============================================================================
#  DELETE VIDEO
# ============================================================================
@media_video.route("/delete/<int:video_id>", methods=["POST"])
def delete_video(video_id):
    cek = BMS_video_required()
    if cek:
        return cek

    conn = get_db_conn()
    conn.execute("DELETE FROM videos WHERE id=?", (video_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "message": "Video dihapus dari library"})


# ============================================================================
#  PLAYER UI
# ============================================================================
@media_video.route("/watch/<int:video_id>")
def BMS_video_watch(video_id):
    cek = BMS_video_required()
    if cek:
        return cek

    conn = get_db_conn()
    row = conn.execute("""
        SELECT id, filename, folder_id 
        FROM videos 
        WHERE id=?
    """, (video_id,)).fetchone()
    conn.close()

    if not row:
        return "Video tidak ditemukan", 404

    return render_template(
        "BMS_video_play.html",
        video_id=row["id"],
        filename=row["filename"],
        folder_id=row["folder_id"]
    )