# ============================================================================
#   BMS MP3 MODULE — DATABASE & HELPER (FINAL)
#   Mengelola:
#     ✔ Koneksi SQLite
#     ✔ Inisialisasi tabel
#     ✔ Migrasi kolom baru
#     ✔ Helper user_id & validasi MP3
# ============================================================================

import os
import sqlite3
from flask import session

from app.BMS_config import DB_PATH, MUSIC_FOLDER
from app.routes.BMS_logger import BMS_write_log

# Pastikan folder media ada
os.makedirs(MUSIC_FOLDER, exist_ok=True)

# Penanda inisialisasi DB (agar tidak jalan berulang)
_db_initialized = False


def get_db():
    """
    Membuka koneksi ke database SQLite dan memastikan struktur tabel siap.
    """
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        try:
            cur = conn.cursor()

            # ================== FOLDER TABLE ==================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mp3_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_name TEXT,
                    folder_path TEXT UNIQUE
                )
            """)

            # ================== TRACK TABLE ==================
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
                    cover_path TEXT,
                    FOREIGN KEY(folder_id)
                        REFERENCES mp3_folders(id)
                        ON DELETE CASCADE
                )
            """)

            conn.commit()

            # ================== MIGRATION CHECK ==================
            existing_cols = [
                r["name"]
                for r in cur.execute(
                    "PRAGMA table_info(mp3_tracks)"
                ).fetchall()
            ]

            add_cols = []

            if "user_id" not in existing_cols:
                add_cols.append(
                    "ALTER TABLE mp3_tracks ADD COLUMN user_id TEXT;"
                )

            if "is_favorite" not in existing_cols:
                add_cols.append(
                    "ALTER TABLE mp3_tracks ADD COLUMN is_favorite INTEGER DEFAULT 0;"
                )

            if "play_count" not in existing_cols:
                add_cols.append(
                    "ALTER TABLE mp3_tracks ADD COLUMN play_count INTEGER DEFAULT 0;"
                )

            if "cover_path" not in existing_cols:
                add_cols.append(
                    "ALTER TABLE mp3_tracks ADD COLUMN cover_path TEXT;"
                )

            for cmd in add_cols:
                try:
                    cur.execute(cmd)
                except Exception:
                    pass  # kolom sudah ada → aman

            conn.commit()
            _db_initialized = True

        except Exception as e:
            BMS_write_log(f"[DB INIT ERROR] {e}", "SYSTEM")

    return conn


# ============================================================================
#   USER IDENTIFIER HELPER
# ============================================================================
def current_user_identifier():
    """
    Mengambil identifier user aktif (multi-user support).
    """
    if session.get("user_id") is not None:
        return str(session.get("user_id"))

    if session.get("username") is not None:
        return str(session.get("username"))

    return "anonymous"


# ============================================================================
#   FILE HELPER
# ============================================================================
def is_mp3(name):
    """
    Cek apakah file adalah MP3.
    """
    return isinstance(name, str) and name.lower().endswith(".mp3")