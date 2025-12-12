import time
from flask import session

# Konstanta default untuk durasi session (dalam menit)
DEFAULT_SESSION_MINUTES = 60

def BMS_auth_is_login():
    """
    Memeriksa apakah user saat ini memiliki session login yang valid.
    
    Fungsi ini melakukan beberapa pengecekan:
    1. Memastikan user_id ada dalam session
    2. Memastikan username ada dalam session
    3. Memeriksa apakah session sudah kadaluarsa berdasarkan timestamp expiry
    
    Returns:
        bool: True jika user memiliki session login yang valid, False jika tidak
    """
    # Cek apakah user_id ada dalam session
    if not session.get("user_id"):
        return False

    # Cek apakah username ada dalam session
    if not session.get("username"):
        return False

    # Ambil timestamp expiry session
    expiry_ts = session.get("_expiry_ts")
    now = int(time.time())

    # Cek apakah session sudah kadaluarsa
    if not expiry_ts or now > int(expiry_ts):
        session.clear()  # Hapus session yang kadaluarsa
        return False

    return True

def BMS_auth_is_admin():
    """
    Memeriksa apakah user yang login memiliki role 'admin'.
    
    Fungsi ini pertama-tama memastikan user sudah login, kemudian
    memeriksa apakah role dalam session adalah 'admin'.
    
    Returns:
        bool: True jika user adalah admin, False jika tidak
    """
    return BMS_auth_is_login() and session.get("role") == "admin"

def BMS_auth_is_root():
    """
    Memeriksa apakah user yang login memiliki role 'root'.
    
    Fungsi ini pertama-tama memastikan user sudah login, kemudian
    memeriksa apakah role dalam session adalah 'root'.
    
    Returns:
        bool: True jika user adalah root, False jika tidak
    """
    return BMS_auth_is_login() and session.get("role") == "root"