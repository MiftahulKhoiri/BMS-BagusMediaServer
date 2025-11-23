import sqlite3
import os

# =====================================================
#  PENGATURAN PATH DATABASE
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bms.db")


# =====================================================
#  KONEKSI DATABASE
# =====================================================
def BMS_db_connect():
    """Membuat koneksi SQLite dengan row dict-like."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
#  INIT DATABASE (DIPANGGIL SAAT APLIKASI START)
# =====================================================
def BMS_db_init():
    """
    Membuat tabel users jika belum ada.
    Dipanggil sekali saat Flask start.
    """

    # Pastikan file bms.db ada di folder yang benar
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "w").close()

    conn = BMS_db_connect()
    cur = conn.cursor()

    # Buat tabel users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =====================================================
#  MEMBUAT ROOT PERTAMA (OPSIONAL)
# =====================================================
def BMS_db_create_root(username, password):
    """
    Membuat akun root pertama.
    Tidak dipakai otomatis karena BMS_auth sudah tangani root pertama.
    Berguna untuk recovery.
    """
    import hashlib

    conn = BMS_db_connect()
    cur = conn.cursor()

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    try:
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed_pw, "root"))

        conn.commit()

    except sqlite3.IntegrityError:
        # Root sudah ada → abaikan saja
        pass

    conn.close()