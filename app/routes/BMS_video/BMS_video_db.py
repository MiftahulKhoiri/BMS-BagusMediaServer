# ============================================================================
#   BMS VIDEO MODULE — DATABASE & BASIC HELPERS
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
    Membuka koneksi SQLite dan memastikan tabel video sudah lengkap.
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
                folder_path TEXT UNIQUE
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
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        _db_initialized = True

    return conn


# ============================================================================
#   LOGIN CHECK HELPERS
# ============================================================================
def video_login_required():
    """Memastikan user login sebelum akses video."""
    if session.get("is_login") != True:
        return False
    return True


# ============================================================================
#   VIDEO FILE VALIDATION
# ============================================================================
VALID_VIDEO_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")


def is_video_file(name):
    return isinstance(name, str) and name.lower().endswith(VALID_VIDEO_EXT)


# ============================================================================
#   SAFE PATH CHECK (should be inside VIDEO_FOLDER)
# ============================================================================
def is_inside_video_folder(path):
    try:
        real = os.path.realpath(path)
        base = os.path.realpath(VIDEO_FOLDER)
        return real.startswith(base)
    except:
        return False