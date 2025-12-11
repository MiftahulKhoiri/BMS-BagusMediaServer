# ============================================================================
# BMS_VIDEO_DB.PY — Database helper untuk Video (FINAL)
# - Koneksi DB
# - Migrasi kolom user_id otomatis
# - Identifier user (support guest fallback)
# - Validasi file & path safety
# ============================================================================

import os
import sqlite3
from flask import session
from app.BMS_config import DB_PATH, VIDEO_FOLDER

# Pastikan folder video ada
os.makedirs(VIDEO_FOLDER, exist_ok=True)

_db_initialized = False

def get_db():
    """
    Buka koneksi dan pastikan struktur tabel sudah sesuai
    (migrasi kolom user_id & index unik untuk folder_path+user_id).
    """
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        cur = conn.cursor()

        # Tabel folders (per-user)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT,
                folder_path TEXT,
                user_id TEXT
            )
        """)

        # Tabel videos (per-user)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT UNIQUE,
                folder_id INTEGER,
                size INTEGER DEFAULT 0,
                added_at TEXT,
                user_id TEXT,
                FOREIGN KEY(folder_id) REFERENCES folders(id)
            )
        """)

        # Pastikan kolom user_id ada (jika DB lama tanpa kolom ini)
        try:
            cols_f = [r["name"] for r in cur.execute("PRAGMA table_info(folders)").fetchall()]
            if "user_id" not in cols_f:
                cur.execute("ALTER TABLE folders ADD COLUMN user_id TEXT")
        except Exception:
            pass

        try:
            cols_v = [r["name"] for r in cur.execute("PRAGMA table_info(videos)").fetchall()]
            if "user_id" not in cols_v:
                cur.execute("ALTER TABLE videos ADD COLUMN user_id TEXT")
        except Exception:
            pass

        # Buat UNIQUE INDEX gabungan (folder_path + user_id) untuk mengizinkan
        # folder_path yang sama dimiliki beberapa user namun unik per user.
        try:
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_folders_path_user
                ON folders(folder_path, user_id)
            """)
        except Exception:
            pass

        # Index untuk videos -> mempercepat query per-user per-folder
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_folder_user
                ON videos(folder_id, user_id)
            """)
        except Exception:
            pass

        conn.commit()
        _db_initialized = True

    return conn


# -------------------------
# Current user identifier
# -------------------------
def current_user_identifier():
    """
    Return a string identifier for current user:
    - use session['user_id'] (if exists) otherwise session['username']
    - if no login, create guest id in session['guest_id'] and return it
    This allows scans to be assigned to a consistent owner even for guests.
    """
    if session.get("user_id") is not None:
        return str(session.get("user_id"))
    if session.get("username") is not None:
        return str(session.get("username"))

    # fallback guest id (persist during session)
    if not session.get("guest_id"):
        import uuid
        session["guest_id"] = "guest-" + uuid.uuid4().hex[:12]
    return session["guest_id"]


# -------------------------
# File validation helpers
# -------------------------
VALID_VIDEO_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")
def is_video_file(name):
    return isinstance(name, str) and name.lower().endswith(VALID_VIDEO_EXT)


def is_inside_video_folder(path):
    try:
        base = os.path.realpath(VIDEO_FOLDER)
        real = os.path.realpath(path)
        return real.startswith(base)
    except:
        return False