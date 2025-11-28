import sqlite3
from app.BMS_config import DB_PATH

def ensure_users_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Buat tabel jika belum ada
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Kolom yang wajib ada
    required_columns = {
        "nama": "TEXT",
        "umur": "TEXT",
        "gender": "TEXT",
        "email": "TEXT",
        "bio": "TEXT",
        "foto_profile": "TEXT",
        "foto_background": "TEXT"
    }

    # Kolom yang tersedia di DB
    cur.execute("PRAGMA table_info(users)")
    existing = [col[1] for col in cur.fetchall()]

    # Tambahkan kolom yang kurang
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

def ensure_root_user():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # cek apakah root sudah ada
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

def ensure_videos_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL UNIQUE,
        size INTEGER DEFAULT 0,
        duration TEXT,
        added_at TEXT
    )
    """)
    conn.commit()
    conn.close()
