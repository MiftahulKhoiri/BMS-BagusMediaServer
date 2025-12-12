import time
from flask import current_app
from .db import get_db

# Konstanta default untuk sistem penguncian akun
DEFAULT_LOCK_THRESHOLD = 5  # Jumlah maksimum percobaan gagal sebelum dikunci
DEFAULT_LOCK_WINDOW_MIN = 15  # Jangka waktu (dalam menit) untuk menghitung percobaan gagal

def add_failed_attempt(username, ip):
    """
    Mencatat percobaan login gagal ke dalam database.
    
    Fungsi ini menyimpan informasi tentang percobaan login yang gagal
    ke tabel 'failed_logins' untuk keperluan pelacakan dan pencegahan
    serangan brute force.
    
    Args:
        username (str): Nama pengguna yang digunakan dalam percobaan login
        ip (str): Alamat IP dari mana percobaan login dilakukan
    
    Returns:
        None: Fungsi ini hanya menambahkan data ke database
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO failed_logins (username, ip, ts) VALUES (?, ?, ?)",
        (username, ip, int(time.time()))
    )
    conn.commit()
    conn.close()

def count_failed_attempts(username, ip, minutes_window):
    """
    Menghitung jumlah percobaan login gagal dalam jangka waktu tertentu.
    
    Fungsi ini menghitung berapa kali pengguna atau IP tertentu
    gagal login dalam rentang waktu yang ditentukan (dalam menit).
    Perhitungan mencakup baik percobaan dengan username spesifik
    maupun dari alamat IP yang sama.
    
    Args:
        username (str): Nama pengguna yang akan dihitung percobaannya
        ip (str): Alamat IP yang akan dihitung percobaannya
        minutes_window (int): Rentang waktu dalam menit untuk menghitung percobaan
    
    Returns:
        int: Jumlah percobaan login gagal dalam jangka waktu yang ditentukan
    """
    cutoff = int(time.time()) - (minutes_window * 60)
    conn = get_db()
    cur = conn.execute("""
        SELECT COUNT(*) as c
        FROM failed_logins
        WHERE (username = ? OR ip = ?) AND ts >= ?
    """, (username, ip, cutoff))
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0

def clear_failed_attempts(username, ip):
    """
    Menghapus riwayat percobaan login gagal untuk pengguna atau IP tertentu.
    
    Fungsi ini digunakan untuk membersihkan riwayat kegagalan login,
    biasanya dipanggil setelah login berhasil untuk mereset counter
    penguncian akun.
    
    Args:
        username (str): Nama pengguna yang akan dihapus riwayatnya
        ip (str): Alamat IP yang akan dihapus riwayatnya
    
    Returns:
        None: Fungsi ini hanya menghapus data dari database
    """
    conn = get_db()
    conn.execute("DELETE FROM failed_logins WHERE username = ? OR ip = ?", (username, ip))
    conn.commit()
    conn.close()

def is_locked(username, ip):
    """
    Memeriksa apakah akun atau IP terkunci karena terlalu banyak percobaan gagal.
    
    Fungsi ini menentukan status penguncian dengan menghitung percobaan login gagal
    dalam jangka waktu tertentu dan membandingkannya dengan threshold yang ditetapkan.
    Threshold dan jangka waktu bisa dikonfigurasi di aplikasi Flask.
    
    Args:
        username (str): Nama pengguna yang akan diperiksa
        ip (str): Alamat IP yang akan diperiksa
    
    Returns:
        bool: True jika akun/IP terkunci, False jika tidak
    """
    # Ambil konfigurasi dari Flask app atau gunakan nilai default
    threshold = current_app.config.get("BMS_LOCK_THRESHOLD", DEFAULT_LOCK_THRESHOLD)
    window = current_app.config.get("BMS_LOCK_WINDOW_MIN", DEFAULT_LOCK_WINDOW_MIN)
    
    # Hitung percobaan gagal dalam jangka waktu tertentu
    attempts = count_failed_attempts(username, ip, window)
    
    # Tentukan status penguncian berdasarkan threshold
    return attempts >= threshold