import os
import sqlite3
from flask import Blueprint, jsonify, request, send_file, session, render_template, Response, current_app
from datetime import datetime

from app.BMS_config import DB_PATH, MUSIC_FOLDER
from app.routes.BMS_auth import BMS_auth_is_login
from app.routes.BMS_logger import BMS_write_log

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")

# pastikan folder musik ada
os.makedirs(MUSIC_FOLDER, exist_ok=True)


# -------------------------
#  DB helper + init once
# -------------------------
_db_initialized = False

def get_db():
    """
    Kembalikan koneksi DB. Jika tabel mp3 tidak ada, buat sekali.
    Juga cek/migrasi kolom tambahan (user_id, is_favorite, play_count).
    """
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        try:
            cur = conn.cursor()
            # Buat tabel jika belum ada
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mp3_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_name TEXT,
                    folder_path TEXT UNIQUE
                )
            """)
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

            # If table existed earlier without new columns, try to add missing columns safely
            # (SQLite doesn't have DROP COLUMN; we only ADD if missing)
            existing_cols = [r['name'] for r in cur.execute("PRAGMA table_info(mp3_tracks)").fetchall()]
            adds = []
            if 'user_id' not in existing_cols:
                adds.append("ALTER TABLE mp3_tracks ADD COLUMN user_id TEXT;")
            if 'is_favorite' not in existing_cols:
                adds.append("ALTER TABLE mp3_tracks ADD COLUMN is_favorite INTEGER DEFAULT 0;")
            if 'play_count' not in existing_cols:
                adds.append("ALTER TABLE mp3_tracks ADD COLUMN play_count INTEGER DEFAULT 0;")
            for a in adds:
                try:
                    cur.execute(a)
                except Exception:
                    # jika gagal (mis. kolom sudah ada), ignore
                    pass
            conn.commit()

            _db_initialized = True
        except Exception as e:
            # log tetapi lanjutkan — operasi lain akan menampilkan error jika DB benar-benar bermasalah
            try:
                BMS_write_log(f"[DB INIT ERROR] {e}", "SYSTEM")
            except:
                print("[DB INIT ERROR]", e)
    return conn


# -------------------------
#  Proteksi Login
# -------------------------
def mp3_required():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    return None


# -------------------------
#  Helper user identifier
# -------------------------
def current_user_identifier():
    """
    Gunakan session['user_id'] jika ada, jika tidak gunakan username.
    Simpan sebagai string untuk fleksibilitas.
    """
    uid = session.get("user_id")
    if uid is not None:
        return str(uid)
    uname = session.get("username")
    if uname is not None:
        return str(uname)
    # fallback
    return "anonymous"


# -------------------------
#  Sanitasi file
# -------------------------
def is_mp3(name):
    return isinstance(name, str) and name.lower().endswith(".mp3")


# -------------------------
#  Safe path check (pastikan file berada di MUSIC_FOLDER)
# -------------------------
def is_inside_music(path):
    try:
        real = os.path.realpath(path)
        music_real = os.path.realpath(MUSIC_FOLDER)
        return real.startswith(music_real)
    except:
        return False


# -------------------------
#  Scan storage (berhati-hati)
# -------------------------
def scan_storage_for_mp3(limit_folders=200, max_files_per_folder=500):
    """
    Scan daftar root umum + MUSIC_FOLDER.
    Batasi jumlah folder yang dikumpulkan agar tidak overload.
    """
    ROOT_SCAN = [
        MUSIC_FOLDER,
        "/storage/emulated/0/Music",
        "/storage/emulated/0/Download",
        "/storage/emulated/0/WhatsApp/Media",
        "/storage/emulated/0/",
    ]

    found = []
    seen = set()

    for base in ROOT_SCAN:
        if len(found) >= limit_folders:
            break
        if not os.path.exists(base):
            continue

        # walk secara perlahan, batasi jumlah file per folder
        try:
            for root, dirs, files in os.walk(base):
                mp3_files = [f for f in files if is_mp3(f)]
                if not mp3_files:
                    continue

                if root in seen:
                    continue

                seen.add(root)
                found.append({
                    "folder_path": root,
                    "folder_name": os.path.basename(root) or root,
                    "files": mp3_files[:max_files_per_folder]
                })

                if len(found) >= limit_folders:
                    break
        except Exception as e:
            try:
                BMS_write_log(f"[SCAN ERROR] {e}", session.get("username", "SYSTEM"))
            except:
                pass

    return found


# ======================================================
#  ROUTE: SCAN + IMPORT TO DB (folder mode)
# ======================================================
@media_mp3.route("/scan-db", methods=["POST"])
def scan_db():
    cek = mp3_required()
    if cek:
        return cek

    username = session.get("username", "UNKNOWN")
    owner = current_user_identifier()

    folders = scan_storage_for_mp3()
    conn = get_db()
    cur = conn.cursor()
    imported = 0

    try:
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            # guard: hanya import jika folder berada di MUSIC_FOLDER
            # jika kamu ingin import dari seluruh storage, ubah sesuai kebutuhan
            if not is_inside_music(folder_path):
                # skip folder di luar MUSIC_FOLDER
                continue

            # masukkan folder jika belum ada
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

            # simpan file mp3 (ikat pada user saat ini)
            for file_name in f["files"]:
                fp = os.path.join(folder_path, file_name)
                try:
                    if not os.path.exists(fp):
                        continue
                    size = os.path.getsize(fp)
                except:
                    continue

                cur.execute("SELECT id FROM mp3_tracks WHERE filepath=? AND user_id=?", (fp, owner))
                if cur.fetchone():
                    continue

                cur.execute("""
                    INSERT INTO mp3_tracks (folder_id, filename, filepath, size, added_at, user_id, is_favorite, play_count)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (folder_id, file_name, fp, size, datetime.utcnow().isoformat(), owner, 0, 0))

                imported += 1
                try:
                    BMS_write_log(f"Import MP3 → {fp}", username)
                except:
                    pass

        conn.commit()
    except Exception as e:
        conn.rollback()
        try:
            BMS_write_log(f"[IMPORT ERROR] {e}", username)
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

    return jsonify({
        "status": "ok",
        "imported": imported,
        "folders_total": len(folders)
    }), 200


# ======================================================
#  LIST FOLDERS (hanya folder yang punya track untuk user ini)
# ======================================================
@media_mp3.route("/folders")
def list_folders():
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()

    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT f.id, f.folder_name,
                   (SELECT COUNT(*) FROM mp3_tracks t WHERE t.folder_id = f.id AND t.user_id = ?) AS total_mp3
            FROM mp3_folders f
            WHERE (SELECT COUNT(*) FROM mp3_tracks t WHERE t.folder_id = f.id AND t.user_id = ?) > 0
            ORDER BY f.folder_name ASC
        """, (owner, owner)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#  LIST TRACKS IN FOLDER (filtered by user)
# ======================================================
@media_mp3.route("/folder/<int:folder_id>/tracks")
def folder_tracks(folder_id):
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()

    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, filename, filepath, size, is_favorite, play_count
            FROM mp3_tracks
            WHERE folder_id=? AND user_id=?
            ORDER BY filename ASC
        """, (folder_id, owner)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#  FAVORITES: list & toggle
# ======================================================
@media_mp3.route("/favorites")
def list_favorites():
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, filename, filepath, size, play_count
            FROM mp3_tracks
            WHERE user_id=? AND is_favorite=1
            ORDER BY filename ASC
        """, (owner,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@media_mp3.route("/favorite/<int:track_id>", methods=["POST"])
def toggle_favorite(track_id):
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()
    username = session.get("username", "UNKNOWN")

    try:
        conn = get_db()
        cur = conn.cursor()
        row = cur.execute("SELECT is_favorite FROM mp3_tracks WHERE id=? AND user_id=?", (track_id, owner)).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Track tidak ditemukan atau bukan milik Anda"}), 404

        new_state = 0 if row["is_favorite"] else 1
        cur.execute("UPDATE mp3_tracks SET is_favorite=? WHERE id=? AND user_id=?", (new_state, track_id, owner))
        conn.commit()
        conn.close()

        try:
            BMS_write_log(f"Favorite toggled → {track_id} = {new_state}", username)
        except:
            pass

        return jsonify({"status": "ok", "is_favorite": new_state}), 200
    except Exception as e:
        try:
            BMS_write_log(f"[FAV ERROR] {e}", username)
        except:
            pass
        return jsonify({"error": str(e)}), 500


# ======================================================
#  TRACK INFO (filtered by user)
# ======================================================
@media_mp3.route("/info/<int:track_id>")
def track_info(track_id):
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()
    try:
        conn = get_db()
        row = conn.execute("""
            SELECT id, filename, filepath, size, is_favorite, play_count
            FROM mp3_tracks
            WHERE id=? AND user_id=?
        """, (track_id, owner)).fetchone()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    return jsonify(dict(row)), 200


# ======================================================
#  STREAM MP3 (support Range header) + increment play_count
# ======================================================
def range_request(file_path):
    """
    Return tuple (start, end, file_size) jika header Range ada,
    atau None jika tidak ada.
    """
    range_header = request.headers.get('Range', None)
    if not range_header:
        return None
    # contoh: Range: bytes=0-1023
    try:
        units, rng = range_header.split('=')
        start_str, end_str = rng.split('-')
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else None
        file_size = os.path.getsize(file_path)
        if end is None or end >= file_size:
            end = file_size - 1
        return start, end, file_size
    except:
        return None


@media_mp3.route("/play/<int:track_id>")
def play_mp3(track_id):
    cek = mp3_required()
    if cek:
        return cek

    owner = current_user_identifier()
    username = session.get("username", "UNKNOWN")

    try:
        conn = get_db()
        row = conn.execute("SELECT filepath, user_id FROM mp3_tracks WHERE id=?", (track_id,)).fetchone()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    # Pastikan track milik user saat ini
    if str(row["user_id"]) != str(owner):
        return jsonify({"error": "Track tidak ditemukan atau bukan milik Anda"}), 404

    fp = row["filepath"]
    if not os.path.exists(fp):
        return jsonify({"error": "File MP3 hilang"}), 404

    # pastikan file berada di folder musik yang diizinkan
    if not is_inside_music(fp):
        return jsonify({"error": "Akses file tidak diizinkan"}), 403

    # Increment play_count (lokal kepada row ini)
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE mp3_tracks SET play_count = COALESCE(play_count,0) + 1 WHERE id=? AND user_id=?", (track_id, owner))
        conn.commit()
        conn.close()
    except Exception:
        pass

    # dukung Range header supaya player bisa seek
    r = range_request(fp)
    if r:
        start, end, file_size = r
        length = end - start + 1
        with open(fp, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        rv = Response(data, 206, mimetype="audio/mpeg", direct_passthrough=True)
        rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(length))
        return rv

    # normal return full file
    try:
        return send_file(fp, mimetype="audio/mpeg", as_attachment=False)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#  PLAYER PAGE & UI
# ======================================================
@media_mp3.route("/watch/<int:track_id>")
def mp3_player(track_id):
    cek = mp3_required()
    if cek:
        return cek
    return render_template("BMS_mp3_play.html")


@media_mp3.route("/")
def mp3_home():
    cek = mp3_required()
    if cek:
        return cek
    return render_template("BMS_mp3.html")