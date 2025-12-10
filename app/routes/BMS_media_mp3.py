# ============================================================================
#   BMS MEDIA SERVER — MP3 MODULE (FINAL VERSION)
#   Fitur:
#     ✔ Scan MP3 dari seluruh storage (model seperti scan video)
#     ✔ Per-user MP3 (user_id)
#     ✔ Favorite (❤️)
#     ✔ Play count
#     ✔ Streaming dengan Range support
#     ✔ Struktur folder otomatis
#     ✔ Komentar lengkap untuk maintenance
# ============================================================================

import os
import sqlite3
from flask import Blueprint, jsonify, request, send_file, session, render_template, Response
from datetime import datetime

# CONFIG
from app.BMS_config import DB_PATH, MUSIC_FOLDER
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")

# Pastikan folder media utama ada
os.makedirs(MUSIC_FOLDER, exist_ok=True)


# ============================================================================
#  DATABASE INITIALIZER
# ============================================================================
_db_initialized = False

def get_db():
    """
    Membuka koneksi SQLite dan sekaligus memastikan tabel sudah lengkap.
    Otomatis membuat tabel dan kolom tambahan bila belum ada.
    """
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        try:
            cur = conn.cursor()

            # Tabel folder
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mp3_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_name TEXT,
                    folder_path TEXT UNIQUE
                )
            """)

            # Tabel track / file
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mp3_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER,
                    filename TEXT,
                    filepath TEXT UNIQUE,
                    size INTEGER,
                    added_at TEXT,
                    user_id TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    play_count INTEGER DEFAULT 0,
                    FOREIGN KEY(folder_id) REFERENCES mp3_folders(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

            # MIGRASI kolom bila belum ada (untuk update versi)
            existing = [r['name'] for r in cur.execute("PRAGMA table_info(mp3_tracks)").fetchall()]
            adds = []

            if "user_id" not in existing:
                adds.append("ALTER TABLE mp3_tracks ADD COLUMN user_id TEXT;")

            if "is_favorite" not in existing:
                adds.append("ALTER TABLE mp3_tracks ADD COLUMN is_favorite INTEGER DEFAULT 0;")

            if "play_count" not in existing:
                adds.append("ALTER TABLE mp3_tracks ADD COLUMN play_count INTEGER DEFAULT 0;")

            for sql in adds:
                try:
                    cur.execute(sql)
                except:
                    pass  # kolom sudah ada

            conn.commit()
            _db_initialized = True

        except Exception as e:
            BMS_write_log(f"[DB INIT ERROR] {e}", "SYSTEM")

    return conn


# ============================================================================
#  PERLINDUNGAN LOGIN
# ============================================================================
def mp3_required():
    """ Menghalangi akses tanpa login """
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    return None


# ============================================================================
#  IDENTITAS USER (DASAR SISTEM PER-USER)
# ============================================================================
def current_user_identifier():
    """
    Mengembalikan ID unik pengguna:
    - Utamakan session['user_id']
    - Jika tidak ada, gunakan username
    """
    if session.get("user_id") is not None:
        return str(session.get("user_id"))

    if session.get("username") is not None:
        return str(session.get("username"))

    return "anonymous"


# ============================================================================
#  MP3 VALIDATOR
# ============================================================================
def is_mp3(name):
    return isinstance(name, str) and name.lower().endswith(".mp3")


# ============================================================================
#  SCAN STORAGE — versi stabil seperti scan video
# ============================================================================
def scan_storage_for_mp3():
    """
    Scan seluruh storage untuk mencari folder yang berisi file MP3.
    Mengikuti konsep scan video:
      - Root utama: /storage/emulated/0
      - Fallback: HOME Termux
      - Limit folder agar tidak hang
    """
    # Root scan utama Android
    ROOT_SCAN = "/storage/emulated/0"

    # Jika tidak tersedia (Termux sandbox), fallback ke HOME
    if not os.path.exists(ROOT_SCAN):
        ROOT_SCAN = os.path.expanduser("~")

    MAX_FOLDERS = 200            # Batas folder agar tidak lemot
    MAX_FILES = 300              # Batas file per folder

    folders = []
    count = 0

    for root, dirs, files in os.walk(ROOT_SCAN):
        if count >= MAX_FOLDERS:
            break

        mp3_files = [f for f in files if is_mp3(f)]
        if not mp3_files:
            continue

        folders.append({
            "folder_path": root,
            "folder_name": os.path.basename(root) or root,
            "files": mp3_files[:MAX_FILES],
        })

        count += 1  # folder valid bertambah

    return folders


# ============================================================================
#  SCAN + IMPORT MP3 KE DATABASE
# ============================================================================
@media_mp3.route("/scan-db", methods=["POST"])
def scan_db():
    """
    Menjalankan scan storage, lalu menyimpan folder & file MP3 ke database.
    Setiap track dikaitkan ke user yang melakukan scan.
    """
    cek = mp3_required()
    if cek:
        return cek

    user = current_user_identifier()
    username = session.get("username", "UNKNOWN")

    BMS_write_log("Memulai scan MP3", username)

    # 1. Dapatkan daftar folder + file yang ditemukan
    folders = scan_storage_for_mp3()

    # 2. Proses simpan ke database
    conn = get_db()
    cur = conn.cursor()

    imported_folders = []
    imported_tracks = []

    try:
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            # Simpan folder bila belum ada
            row = cur.execute(
                "SELECT id FROM mp3_folders WHERE folder_path=?",
                (folder_path,)
            ).fetchone()

            if row:
                folder_id = row["id"]
            else:
                cur.execute("""
                    INSERT INTO mp3_folders (folder_name, folder_path)
                    VALUES (?,?)
                """, (folder_name, folder_path))

                folder_id = cur.lastrowid
                imported_folders.append(folder_name)

            # Simpan file MP3 yang ada pada folder
            for fn in f["files"]:
                fp = os.path.join(folder_path, fn)
                if not os.path.exists(fp):
                    continue

                # Skip jika sudah ada untuk user ini
                exists = cur.execute("""
                    SELECT id FROM mp3_tracks WHERE filepath=? AND user_id=?
                """, (fp, user)).fetchone()

                if exists:
                    continue

                size = os.path.getsize(fp)
                added = datetime.utcnow().isoformat()

                cur.execute("""
                    INSERT INTO mp3_tracks
                    (folder_id, filename, filepath, size, added_at, user_id)
                    VALUES (?,?,?,?,?,?)
                """, (
                    folder_id, fn, fp, size,
                    added, user
                ))

                imported_tracks.append(fn)

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": imported_folders,
        "tracks_added": imported_tracks,
        "message": f"{len(imported_folders)} folder & {len(imported_tracks)} MP3 baru."
    })


# ============================================================================
#  LIST FOLDERS MILIK USER
# ============================================================================
@media_mp3.route("/folders")
def list_folders():
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()

    conn = get_db()
    rows = conn.execute("""
        SELECT f.id, f.folder_name,
               (SELECT COUNT(*) FROM mp3_tracks t
                WHERE t.folder_id = f.id AND t.user_id = ?) AS total_mp3
        FROM mp3_folders f
        WHERE (SELECT COUNT(*) FROM mp3_tracks t 
               WHERE t.folder_id = f.id AND t.user_id = ?) > 0
        ORDER BY f.folder_name ASC
    """, (owner, owner)).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================================
#  LIST TRACKS DALAM FOLDER
# ============================================================================
@media_mp3.route("/folder/<int:folder_id>/tracks")
def folder_tracks(folder_id):
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()

    conn = get_db()
    rows = conn.execute("""
        SELECT id, filename, filepath, size, is_favorite, play_count
        FROM mp3_tracks
        WHERE folder_id=? AND user_id=?
        ORDER BY filename ASC
    """, (folder_id, owner)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ============================================================================
#  FAVORITE LIST
# ============================================================================
@media_mp3.route("/favorites")
def list_favorites():
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()
    conn = get_db()

    rows = conn.execute("""
        SELECT id, filename, filepath, size, play_count
        FROM mp3_tracks
        WHERE user_id=? AND is_favorite=1
        ORDER BY filename ASC
    """, (owner,)).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================================
#  TOGGLE FAVORITE
# ============================================================================
@media_mp3.route("/favorite/<int:track_id>", methods=["POST"])
def toggle_favorite(track_id):
    cek = mp3_required()
    if cek:
        return cek

    user = current_user_identifier()

    conn = get_db()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT is_favorite
        FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, user)).fetchone()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    new_state = 0 if row["is_favorite"] else 1

    cur.execute("""
        UPDATE mp3_tracks SET is_favorite=?
        WHERE id=? AND user_id=?
    """, (new_state, track_id, user))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "is_favorite": new_state})


# ============================================================================
#  TRACK INFO
# ============================================================================
@media_mp3.route("/info/<int:track_id>")
def track_info(track_id):
    cek = mp3_required()
    if cek:
        return cek

    user = current_user_identifier()
    conn = get_db()

    row = conn.execute("""
        SELECT id, filename, filepath, size, is_favorite, play_count
        FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, user)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    return jsonify(dict(row))


# ============================================================================
#  STREAM MP3 + PLAY COUNT
# ============================================================================
def range_request(file_path):
    """ Mengambil header Range untuk streaming video/audio """
    header = request.headers.get("Range")
    if not header:
        return None

    try:
        units, rng = header.split("=")
        start_str, end_str = rng.split("-")
        start = int(start_str) if start_str else 0
        size = os.path.getsize(file_path)
        end = int(end_str) if end_str else size - 1
        return start, end, size
    except:
        return None


@media_mp3.route("/play/<int:track_id>")
def play_mp3(track_id):
    cek = mp3_required()
    if cek:
        return cek

    user = current_user_identifier()

    conn = get_db()
    row = conn.execute("""
        SELECT filepath FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, user)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    fp = row["filepath"]
    if not os.path.exists(fp):
        return jsonify({"error": "File hilang di storage"}), 404

    # Tambah play count
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE mp3_tracks SET play_count = play_count + 1
            WHERE id=? AND user_id=?
        """, (track_id, user))
        conn.commit()
        conn.close()
    except:
        pass

    # Range streaming (untuk seek)
    r = range_request(fp)
    if r:
        start, end, size = r
        length = end - start + 1

        with open(fp, "rb") as f:
            f.seek(start)
            data = f.read(length)

        resp = Response(data, 206, mimetype="audio/mpeg", direct_passthrough=True)
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(length))
        return resp

    # Streaming full file
    return send_file(fp, mimetype="audio/mpeg", as_attachment=False)


# ============================================================================
#  PAGE RENDER
# ============================================================================
@media_mp3.route("/")
def mp3_home():
    cek = mp3_required()
    if cek:
        return cek
    return render_template("BMS_mp3.html")


@media_mp3.route("/watch/<int:track_id>")
def mp3_player(track_id):
    cek = mp3_required()
    if cek:
        return cek
    return render_template("BMS_mp3_play.html")