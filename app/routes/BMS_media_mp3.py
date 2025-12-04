import os
import sqlite3
from flask import Blueprint, jsonify, request, send_file, session, render_template
from datetime import datetime

from app.BMS_config import DB_PATH, MUSIC_FOLDER 
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")

os.makedirs(MUSIC_FOLDER, exist_ok=True)


# ======================================================
#  DB Helper
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#  Proteksi Login
# ======================================================
def mp3_required():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    return None


# ======================================================
#  Sanitasi File
# ======================================================
def is_mp3(name):
    return name.lower().endswith(".mp3")


# ======================================================
#  SCAN STORAGE → FOLDER GROUPING
# ======================================================
def scan_storage_for_mp3():
    ROOT_SCAN = [
        "/storage/emulated/0/Music",
        "/storage/emulated/0/Download",
        "/storage/emulated/0/WhatsApp/Media",
        "/storage/emulated/0/",
        MUSIC_FOLDER
    ]

    found = []

    for base in ROOT_SCAN:
        if not os.path.exists(base):
            continue

        for root, dirs, files in os.walk(base):
            mp3_files = [f for f in files if is_mp3(f)]
            if len(mp3_files) == 0:
                continue

            found.append({
                "folder_path": root,
                "folder_name": os.path.basename(root),
                "files": mp3_files
            })

    return found


# ======================================================
#  ROUTE: SCAN + SAVE ke DATABASE (FOLDER MODE)
# ======================================================
@media_mp3.route("/scan-db", methods=["POST"])
def scan_db():
    cek = mp3_required()
    if cek:
        return cek

    username = session.get("username")

    folders = scan_storage_for_mp3()
    conn = get_db()
    cur = conn.cursor()

    imported = 0

    for f in folders:
        folder_path = f["folder_path"]
        folder_name = f["folder_name"]

        # Masukkan folder jika belum ada
        cur.execute("SELECT id FROM mp3_folders WHERE folder_path=?", (folder_path,))
        row = cur.fetchone()
        if row:
            folder_id = row["id"]
        else:
            cur.execute(
                "INSERT INTO mp3_folders (folder_name, folder_path) VALUES (?,?)",
                (folder_name, folder_path)
            )
            folder_id = cur.lastrowid

        # Simpan file MP3
        for file_name in f["files"]:
            fp = os.path.join(folder_path, file_name)
            size = os.path.getsize(fp)

            cur.execute("SELECT id FROM mp3_tracks WHERE filepath=?", (fp,))
            if cur.fetchone():
                continue

            cur.execute("""
                INSERT INTO mp3_tracks (folder_id, filename, filepath, size, added_at)
                VALUES (?,?,?,?,?)
            """, (folder_id, file_name, fp, size, datetime.utcnow().isoformat()))

            imported += 1
            BMS_write_log(f"Import MP3 → {fp}", username)

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "imported": imported,
        "folders_total": len(folders)
    })


# ======================================================
#  LIST FOLDER MP3
# ======================================================
@media_mp3.route("/folders")
def list_folders():
    cek = mp3_required()
    if cek:
        return cek

    conn = get_db()
    rows = conn.execute("""
        SELECT id, folder_name,
               (SELECT COUNT(*) FROM mp3_tracks WHERE folder_id = mp3_folders.id) AS total_mp3
        FROM mp3_folders
        ORDER BY folder_name ASC
    """).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ======================================================
#  LIST MP3 DALAM FOLDER
# ======================================================
@media_mp3.route("/folder/<int:folder_id>/tracks")
def folder_tracks(folder_id):
    cek = mp3_required()
    if cek:
        return cek

    conn = get_db()
    rows = conn.execute("""
        SELECT id, filename, filepath, size
        FROM mp3_tracks
        WHERE folder_id=?
        ORDER BY filename ASC
    """, (folder_id,)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ======================================================
#  INFORMASI TRACK
# ======================================================
@media_mp3.route("/info/<int:track_id>")
def track_info(track_id):
    cek = mp3_required()
    if cek:
        return cek

    conn = get_db()
    row = conn.execute("SELECT * FROM mp3_tracks WHERE id=?", (track_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    return jsonify(dict(row))


# ======================================================
#  STREAM MP3
# ======================================================
@media_mp3.route("/play/<int:track_id>")
def play_mp3(track_id):
    cek = mp3_required()
    if cek:
        return cek

    conn = get_db()
    row = conn.execute("SELECT filepath FROM mp3_tracks WHERE id=?", (track_id,)).fetchone()
    conn.close()

    if not row:
        return "Track tidak ditemukan", 404

    fp = row["filepath"]
    if not os.path.exists(fp):
        return "File MP3 hilang", 404

    return send_file(fp)


# ======================================================
#  HALAMAN PLAYER MP3
# ======================================================
@media_mp3.route("/watch/<int:track_id>")
def mp3_player(track_id):
    cek = mp3_required()
    if cek:
        return cek

    return render_template("BMS_mp3_play.html")

# ======================================================
#  HALAMAN UI MP3 LIST (BMS_mp3.html)
# ======================================================
@media_mp3.route("/")
def mp3_home():
    cek = mp3_required()
    if cek:
        return cek

    return render_template("BMS_mp3.html")