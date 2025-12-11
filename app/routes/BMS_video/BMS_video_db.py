# ============================================================================
#   BMS VIDEO MODULE — DATABASE & USER SYSTEM (FINAL, NO LOGIN BLOCK)
# ============================================================================

import os
import sqlite3
from flask import session
from app.BMS_config import DB_PATH, VIDEO_FOLDER

# Pastikan folder video ada
os.makedirs(VIDEO_FOLDER, exist_ok=True)

_db_init = False


def get_db():
    """Koneksi SQLite + migrasi kolom user_id otomatis."""
    global _db_init
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_init:
        cur = conn.cursor()

        # ========= Tabel Folders (Video) ==========
        cur.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT,
                folder_path TEXT,
                user_id TEXT
            )
        """)

        # Tambahkan kolom jika belum ada
        cols = [c["name"] for c in cur.execute("PRAGMA table_info(folders)").fetchall()]
        if "user_id" not in cols:
            cur.execute("ALTER TABLE folders ADD COLUMN user_id TEXT")

        # ========= Tabel Videos (Video) ==========
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

        cols_v = [c["name"] for c in cur.execute("PRAGMA table_info(videos)").fetchall()]
        if "user_id" not in cols_v:
            cur.execute("ALTER TABLE videos ADD COLUMN user_id TEXT")

        conn.commit()
        _db_init = True

    return conn


# ============================================================================
#   USER IDENTIFIER (Tidak memaksa login)
# ============================================================================
def current_user_identifier():
    """Jika user login → pakai session user_id atau username.
       Jika tidak login → fallback ID 'guest-<session_id>' """
    if session.get("user_id"):
        return str(session["user_id"])

    if session.get("username"):
        return str(session["username"])

    # fallback untuk user belum login
    if not session.get("guest_id"):
        import uuid
        session["guest_id"] = "guest-" + uuid.uuid4().hex[:12]

    return session["guest_id"]


# ============================================================================
#   FILE VALIDATION
# ============================================================================
VALID_VIDEO_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")


def is_video_file(name):
    return isinstance(name, str) and name.lower().endswith(VALID_VIDEO_EXT)


# ============================================================================
#   SAFE PATH
# ============================================================================
def is_inside_video_folder(path):
    base = os.path.realpath(VIDEO_FOLDER)
    real = os.path.realpath(path)
    return real.startswith(base)