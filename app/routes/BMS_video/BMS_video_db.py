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

# Variabel untuk menandai apakah database sudah diinisialisasi
_db_initialized = False

def get_db():
    """
    Membuka koneksi ke database SQLite dan memastikan struktur tabel sudah sesuai.
    
    Fungsi ini menjalankan inisialisasi tabel dan migrasi kolom jika diperlukan,
    termasuk menambahkan kolom user_id dan indeks untuk performa query.
    
    Returns:
        sqlite3.Connection: Objek koneksi database yang sudah dikonfigurasi
    """
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        cur = conn.cursor()

        # ============ TABEL FOLDERS (PER-USER) ============
        # Tabel untuk menyimpan folder yang berisi video
        cur.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT,
                folder_path TEXT,
                user_id TEXT
            )
        """)

        # ============ TABEL VIDEOS (PER-USER) ============
        # Tabel untuk menyimpan informasi video dengan relasi ke tabel folders
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

        # ============ MIGRASI KOLOM USER_ID ============
        # Pastikan kolom user_id ada di tabel folders (untuk database lama)
        try:
            cols_f = [r["name"] for r in cur.execute("PRAGMA table_info(folders)").fetchall()]
            if "user_id" not in cols_f:
                cur.execute("ALTER TABLE folders ADD COLUMN user_id TEXT")
        except Exception:
            pass  # Kolom mungkin sudah ada

        # Pastikan kolom user_id ada di tabel videos (untuk database lama)
        try:
            cols_v = [r["name"] for r in cur.execute("PRAGMA table_info(videos)").fetchall()]
            if "user_id" not in cols_v:
                cur.execute("ALTER TABLE videos ADD COLUMN user_id TEXT")
        except Exception:
            pass  # Kolom mungkin sudah ada

        # ============ INDEKS UNTUK OPTIMASI QUERY ============
        # Buat indeks unik gabungan (folder_path + user_id) untuk memastikan
        # folder_path dapat sama untuk user berbeda, tetapi unik per user
        try:
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_folders_path_user
                ON folders(folder_path, user_id)
            """)
        except Exception:
            pass  # Indeks mungkin sudah ada

        # Buat indeks untuk mempercepat query video berdasarkan folder_id dan user_id
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_folder_user
                ON videos(folder_id, user_id)
            """)
        except Exception:
            pass  # Indeks mungkin sudah ada

        conn.commit()
        _db_initialized = True  # Tandai bahwa inisialisasi sudah dilakukan

    return conn


# -------------------------
# Current user identifier
# -------------------------
def current_user_identifier():
    """
    Mengembalikan identifier unik untuk user yang sedang aktif.
    
    Prioritas:
    1. user_id dari session (jika ada, biasanya dari user yang login)
    2. username dari session (jika user_id tidak ada)
    3. guest_id dari session (jika tidak ada login, buat ID tamu tetap di session)
    
    Returns:
        str: Identifier user (user_id, username, atau guest_id)
    """
    if session.get("user_id") is not None:
        return str(session.get("user_id"))
    if session.get("username") is not None:
        return str(session.get("username"))

    # Fallback untuk guest (pengguna tanpa login)
    # Buat guest_id di session jika belum ada untuk menjaga konsistensi selama sesi
    if not session.get("guest_id"):
        import uuid
        session["guest_id"] = "guest-" + uuid.uuid4().hex[:12]
    return session["guest_id"]


# -------------------------
# File validation helpers
# -------------------------
# Daftar ekstensi video yang dianggap valid
VALID_VIDEO_EXT = (".mp4", ".mkv", ".webm", ".avi", ".mov")

def is_video_file(name):
    """
    Memeriksa apakah sebuah file adalah file video berdasarkan ekstensinya.
    
    Args:
        name (str): Nama file yang akan diperiksa
    
    Returns:
        bool: True jika file memiliki ekstensi video yang valid (case-insensitive), False jika tidak
    """
    return isinstance(name, str) and name.lower().endswith(VALID_VIDEO_EXT)


def is_inside_video_folder(path):
    """
    Memeriksa apakah path file berada di dalam folder video yang ditentukan (VIDEO_FOLDER).
    
    Fungsi ini untuk keamanan, memastikan file yang diakses tidak keluar dari folder yang diizinkan.
    
    Args:
        path (str): Path file yang akan diperiksa
    
    Returns:
        bool: True jika file berada di dalam VIDEO_FOLDER atau subfoldernya, False jika tidak
    """
    try:
        base = os.path.realpath(VIDEO_FOLDER)  # Path absolut kanonis dari VIDEO_FOLDER
        real = os.path.realpath(path)          # Path absolut kanonis dari file
        return real.startswith(base)
    except:
        return False  # Jika terjadi error (misal path tidak valid), kembalikan False