import sqlite3
from app.BMS_config import DB_PATH

# ================================================================================
#   BMS AUTO REPAIR — FINAL VERSION (USERS + MP3 + VIDEO)
#   Sistem migrasi database otomatis, aman, tidak merusak data lama.
#
#   Tabel yang diperbaiki:
#     ✔ users
#     ✔ folders (VIDEO)
#     ✔ videos (VIDEO)
#     ✔ mp3_folders
#     ✔ mp3_tracks
# ================================================================================


# ================================================================================
# 1. USERS TABLE
# ================================================================================
def ensure_users_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tabel dasar
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # Kolom tambahan untuk profil lengkap (mirip sosial media)
    required_columns = {
        "nama": "TEXT",
        "umur": "TEXT",
        "gender": "TEXT",
        "email": "TEXT",
        "bio": "TEXT",
        "foto_profile": "TEXT",
        "foto_background": "TEXT"
    }

    cur.execute("PRAGMA table_info(users)")
    existing_cols = [col[1] for col in cur.fetchall()]

    for col, tipe in required_columns.items():
        if col not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {tipe}")
                print(f"[DB FIX] Kolom 'users.{col}' ditambahkan.")
            except Exception as e:
                print(f"[DB FIX] Gagal menambah kolom users.{col}: {e}")

    conn.commit()
    conn.close()
    print("[DB FIX] Users table repair complete.")


# ================================================================================
# 2. CREATE ROOT USER (jika tidak ada)
# ================================================================================
def ensure_root_user():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username='root'")
    exists = cur.fetchone()

    if exists:
        print("[DB FIX] User root sudah ada.")
        conn.close()
        return

    from werkzeug.security import generate_password_hash
    pw_hash = generate_password_hash("root123")

    cur.execute("""
        INSERT INTO users (username, password, role, nama)
        VALUES (?, ?, ?, ?)
    """, ("root", pw_hash, "root", "System Root"))

    conn.commit()
    conn.close()
    print("[DB FIX] User ROOT berhasil dibuat.")


# ================================================================================
# 3. VIDEO — TABLE FOLDERS (PER-USER)
# ================================================================================
def ensure_folders_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_name TEXT,
            folder_path TEXT,
            user_id TEXT
        )
    """)

    cur.execute("PRAGMA table_info(folders)")
    existing = [col[1] for col in cur.fetchall()]

    if "user_id" not in existing:
        try:
            cur.execute("ALTER TABLE folders ADD COLUMN user_id TEXT")
            print("[DB FIX] folders.user_id ditambahkan.")
        except Exception as e:
            print("[DB FIX] Error tambah folders.user_id:", e)

    conn.commit()
    conn.close()
    print("[DB FIX] Folders table ensured.")


# ================================================================================
# 4. VIDEO — TABLE VIDEOS (PER-USER)
# ================================================================================
def ensure_videos_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tabel dasar (sekarang pakai user_id)
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

    cur.execute("PRAGMA table_info(videos)")
    existing = [col[1] for col in cur.fetchall()]

    required = {
        "folder_id": "INTEGER",
        "size": "INTEGER DEFAULT 0",
        "added_at": "TEXT",
        "user_id": "TEXT"
    }

    for col, tipe in required.items():
        if col not in existing:
            try:
                cur.execute(f"ALTER TABLE videos ADD COLUMN {col} {tipe}")
                print(f"[DB FIX] videos.{col} ditambahkan.")
            except Exception as e:
                print(f"[DB FIX] Error tambah videos.{col}: {e}")

    conn.commit()
    conn.close()
    print("[DB FIX] Videos table repair complete.")


# ================================================================================
# 5. MP3 — TABLE mp3_folders
# ================================================================================
def ensure_mp3_tables():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("[DB FIX] Memeriksa tabel MP3...")

    # ----------------------------
    # TABLE: mp3_folders
    # ----------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mp3_folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_name TEXT,
            folder_path TEXT UNIQUE,
            user_id TEXT
        )
    """)

    cur.execute("PRAGMA table_info(mp3_folders)")
    existing_f = [col[1] for col in cur.fetchall()]

    if "user_id" not in existing_f:
        try:
            cur.execute("ALTER TABLE mp3_folders ADD COLUMN user_id TEXT")
            print("[DB FIX] mp3_folders.user_id ditambahkan.")
        except Exception as e:
            print("[DB FIX] Error tambah mp3_folders.user_id:", e)

    # ----------------------------
    # TABLE: mp3_tracks
    # ----------------------------
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
            FOREIGN KEY(folder_id) REFERENCES mp3_folders(id)
        )
    """)

    cur.execute("PRAGMA table_info(mp3_tracks)")
    existing_t = [col[1] for col in cur.fetchall()]

    required_cols = {
        "user_id": "TEXT",
        "is_favorite": "INTEGER DEFAULT 0",
        "play_count": "INTEGER DEFAULT 0"
    }

    for col, tipe in required_cols.items():
        if col not in existing_t:
            try:
                cur.execute(f"ALTER TABLE mp3_tracks ADD COLUMN {col} {tipe}")
                print(f"[DB FIX] mp3_tracks.{col} ditambahkan.")
            except Exception as e:
                print(f"[DB FIX] Error tambah mp3_tracks.{col}: {e}")

    conn.commit()
    conn.close()
    print("[DB FIX] Tabel MP3 selesai dicek / diperbaiki.")


# ================================================================================
# 6. AUTO-REPAIR WRAPPER
# ================================================================================
def auto_repair_database():
    ensure_users_table()
    ensure_root_user()
    ensure_folders_table()
    ensure_videos_table()
    ensure_mp3_tables()