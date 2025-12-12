import sqlite3
from app.BMS_config import DB_PATH

def get_db():
    """
    Membuat dan mengembalikan koneksi database SQLite dengan konfigurasi optimal.
    
    Fungsi ini membuat koneksi ke database SQLite menggunakan path dari konfigurasi.
    Menggunakan PARSE_DECLTYPES dan PARSE_COLNAMES untuk konversi tipe data otomatis,
    dan mengatur row_factory ke sqlite3.Row agar hasil query bisa diakses seperti dictionary.
    
    Returns:
        sqlite3.Connection: Objek koneksi database yang sudah dikonfigurasi
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_auth_tables():
    """
    Memastikan tabel untuk autentikasi (failed_logins) ada dalam database.
    
    Fungsi ini membuat tabel 'failed_logins' jika belum ada, yang digunakan untuk
    mencatat percobaan login gagal. Tabel ini berfungsi sebagai bagian dari sistem
    keamanan untuk melacak dan mencegah serangan brute force.
    
    Struktur tabel:
        - id: Primary key auto-increment
        - username: Nama pengguna yang gagal login
        - ip: Alamat IP dari percobaan login
        - ts: Timestamp (waktu) percobaan login dalam format integer
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS failed_logins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        ip TEXT,
        ts INTEGER
    )
    """)
    conn.commit()
    conn.close()

# Jalankan saat import
# Memastikan tabel-tabel yang diperlukan sudah ada ketika modul ini di-load
ensure_auth_tables()