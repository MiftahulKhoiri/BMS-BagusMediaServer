# ============================================================================
#   BMS VIDEO MODULE — DATABASE & USER CONTROL (FINAL)
#   Menangani:
#     ✔ Koneksi DB
#     ✔ Tabel folders + videos
#     ✔ Tambah kolom user_id (jika belum ada)
#     ✔ Helper user_id & validasi
# ============================================================================

import os
import sqlite3
from flask import session
from datetime import datetime

from app.BMS_config import DB_PATH, VIDEO_FOLDER
from app.routes.BMS_logger import BMS_write_log

# Pastikan folder video ada
os.makedirs(VIDEO_FOLDER, exist_ok=True)

_db_initialized = False


def get_db():
    """
    Membuka koneksi SQLite dan memastikan tabel video siap
    + migrasi kolom user_id jika belum ada.
    """
    global _db_initialized

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        cur = conn.cursor()

        # Folder table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT,
                folder_path TEXT UNIQUE,
                user_id TEXT
            )
        """)

        # Video table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT UNIQUE,
                folder_id INTEGER,
                size INTEGER,
                added_at TEXT,
                user_id TEXT,
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """)

        # MIGRASI jika user_id belum ada
        existing_cols = [r["name"] for r in cur.execute("PRAGMA table_info(folders)").fetchall()]
        if "user_id" not in existing_cols:
            cur.execute("ALTER TABLE folders ADD COLUMN user_id TEXT;")

        existing_cols_v = [r["name"] for r in cur.execute("PRAGMA table_info(videos)").fetchall()]
        if "user_id" not in existing_cols_v:
            cur.execute("ALTER TABLE videos ADD COLUMN user_id TEXT;")

        conn.commit()
        _db_initialized = True

    return conn


# ============================================================================
#   USER IDENTIFIER
#   Video sekarang per-user, sama seperti modul MP3
# ===========================================================================
def current_user_identifier():
    """
    Mengembalikan ID unik user, sama seperti modul MP3.
    Terjamin tidak None dan konsisten.
    """
    if session.get("user_id") is not None:
        return str(session.get("user_id"))

    if session.get("username") is not None:
        return str(session.get("username"))

    # fallback aman jika tidak login
    return "anonymous"

# ============================================================================
#   LOGIN CHECK
# ============================================================================
def video_login_required():
    return session.get("is_login") == True


# ============================================================================
#   FILE VALIDATION
# ============================================================================
VALID_VIDEO_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")


def is_video_file(name):
    return isinstance(name, str) and name.lower().endswith(VALID_VIDEO_EXT)


# ============================================================================
#   PATH SAFETY
# ============================================================================
def is_inside_video_folder(path):
    try:
        base = os.path.realpath(VIDEO_FOLDER)
        real = os.path.realpath(path)
        return real.startswith(base)
    except:
        return False