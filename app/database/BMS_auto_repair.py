import sqlite3
from app.BMS_config import DB_PATH

# ======================================================
# 1. REPAIR TABLE USERS
# ======================================================
def ensure_users_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

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
    existing = [col[1] for col in cur.fetchall()]

    for col, tipe in required_columns.items():
        if col not in existing:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {tipe}")
                print(f"[DB FIX] Kolom '{col}' ditambahkan.")
            except Exception as e:
                print(f"[DB FIX] Gagal tambah '{col}': {e}")

    conn.commit()
    conn.close()
    print("[DB FIX] Users table repair complete.")


# ======================================================
# 2. PASTIKAN USER ROOT ADA
# ======================================================
def ensure_root_user():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username='root'")
    user = cur.fetchone()

    if not user:
        cur.execute("""
            INSERT INTO users (username, password, role, nama)
            VALUES ('root', 'root123', 'root', 'System Root')
        """)
        print("[DB FIX] User ROOT dibuat: username=root password=root123")
    else:
        print("[DB FIX] User ROOT sudah ada.")

    conn.commit()
    conn.close()


# ======================================================
# 3. TABEL FOLDERS (BARU)
# ======================================================
def ensure_folders_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_name TEXT,
        folder_path TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()
    print("[DB FIX] Folders table ensured.")


# ======================================================
# 4. TABEL VIDEOS + TAMBAH KOLUM folder_id
# ======================================================
def ensure_videos_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Buat tabel videos jika belum ada
    cur.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filepath TEXT UNIQUE,
        folder_id INTEGER,
        size INTEGER DEFAULT 0,
        duration TEXT,
        added_at TEXT,
        FOREIGN KEY(folder_id) REFERENCES folders(id)
    )
    """)

    # Periksa kolom pada tabel videos
    cur.execute("PRAGMA table_info(videos)")
    existing_cols = [col[1] for col in cur.fetchall()]

    # Kolom wajib
    required_cols = {
        "folder_id": "INTEGER",
        "size": "INTEGER DEFAULT 0",
        "duration": "TEXT",
        "added_at": "TEXT"
    }

    for col, tipe in required_cols.items():
        if col not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE videos ADD COLUMN {col} {tipe}")
                print(f"[DB FIX] Kolom 'videos.{col}' ditambahkan.")
            except Exception as e:
                print(f"[DB FIX] Gagal menambah kolom {col}: {e}")

    conn.commit()
    conn.close()
    print("[DB FIX] Videos table repair complete.")