# ============================================================================
#   BMS MP3 MODULE — DATABASE & HELPER (FINAL)
#   Bagian ini mengelola:
#     ✔ Koneksi SQLite
#     ✔ Inisialisasi tabel
#     ✔ Migrasi kolom baru
#     ✔ Helper user_id & validasi MP3
# ============================================================================

import os
import sqlite3
from datetime import datetime
from flask import session

from app.BMS_config import DB_PATH, MUSIC_FOLDER
from app.routes.BMS_logger import BMS_write_log

# Pastikan folder media ada
os.makedirs(MUSIC_FOLDER, exist_ok=True)

# Variabel untuk menandai apakah database sudah diinisialisasi
_db_initialized = False


def get_db():
    """
    Membuka koneksi ke database SQLite dan memastikan tabel-tabel yang diperlukan tersedia.
    
    Fungsi ini:
    1. Membuat koneksi ke database dengan konfigurasi yang aman untuk multi-thread
    2. Memastikan tabel mp3_folders dan mp3_tracks sudah dibuat
    3. Melakukan migrasi untuk menambahkan kolom baru jika belum ada
    4. Hanya menjalankan inisialisasi sekali selama aplikasi berjalan
    
    Returns:
        sqlite3.Connection: Objek koneksi database yang sudah dikonfigurasi
    """
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        try:
            cur = conn.cursor()

            # ============ FOLDER TABLE ============
            # Membuat tabel untuk menyimpan folder musik jika belum ada
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mp3_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_name TEXT,
                    folder_path TEXT UNIQUE
                )
            """)

            # ============ TRACK TABLE ============
            # Membuat tabel untuk menyimpan track musik jika belum ada
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
                    FOREIGN KEY(folder_id)
                        REFERENCES mp3_folders(id)
                        ON DELETE CASCADE
                )
            """)

            conn.commit()

            # ============ MIGRATION CHECK ============
            # Mengecek struktur tabel mp3_tracks untuk memastikan kolom-kolom baru ada
            existing_cols = [
                r["name"] for r in cur.execute("PRAGMA table_info(mp3_tracks)").fetchall()
            ]

            # Daftar perintah ALTER TABLE untuk menambahkan kolom yang belum ada
            add_cols = []
            if "user_id" not in existing_cols:
                add_cols.append("ALTER TABLE mp3_tracks ADD COLUMN user_id TEXT;")
            if "is_favorite" not in existing_cols:
                add_cols.append("ALTER TABLE mp3_tracks ADD COLUMN is_favorite INTEGER DEFAULT 0;")
            if "play_count" not in existing_cols:
                add_cols.append("ALTER TABLE mp3_tracks ADD COLUMN play_count INTEGER DEFAULT 0;")

            # Eksekusi setiap perintah ALTER TABLE dengan error handling
            for cmd in add_cols:
                try:
                    cur.execute(cmd)
                except:
                    pass  # Jika kolom sudah ada, abaikan error

            conn.commit()
            _db_initialized = True  # Tandai bahwa inisialisasi sudah dilakukan

        except Exception as e:
            # Log error jika terjadi masalah saat inisialisasi database
            BMS_write_log(f"[DB INIT ERROR] {e}", "SYSTEM")

    return conn


# ============================================================================
#   USER IDENTIFIER HELPER
# ============================================================================
def current_user_identifier():
    """
    Mendapatkan identifier unik untuk user yang sedang aktif.
    
    Sistem MP3 dirancang untuk mendukung multi-user, sehingga setiap track
    harus memiliki pemilik (owner). Fungsi ini mengembalikan:
    1. user_id dari session jika tersedia
    2. username dari session jika user_id tidak tersedia
    3. "anonymous" jika tidak ada session user
    
    Returns:
        str: Identifier user (user_id, username, atau "anonymous")
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
    Memeriksa apakah sebuah file adalah file MP3 berdasarkan ekstensinya.
    
    Args:
        name (str): Nama file yang akan diperiksa
    
    Returns:
        bool: True jika file memiliki ekstensi .mp3 (case-insensitive), False jika tidak
    """
    return isinstance(name, str) and name.lower().endswith(".mp3")