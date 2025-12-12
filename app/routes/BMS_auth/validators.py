import re

# Konstanta untuk validasi password: panjang minimal password
PASSWORD_MIN_LENGTH = 8

# Pola regex untuk validasi username:
# - ^ : awal string
# - [A-Za-z0-9_] : hanya huruf besar/kecil, angka, dan underscore
# - {3,32} : panjang antara 3 hingga 32 karakter
# - $ : akhir string
_username_re = re.compile(r'^[A-Za-z0-9_]{3,32}$')

def valid_username(username):
    """
    Memvalidasi format username.
    
    Fungsi ini memeriksa apakah username:
    1. Tidak kosong (truthy)
    2. Sesuai dengan pola regex yang ditentukan (3-32 karakter alfanumerik dan underscore)
    
    Args:
        username (str): Username yang akan divalidasi
    
    Returns:
        bool: True jika username valid, False jika tidak valid
    """
    return bool(username and _username_re.match(username))

def valid_password(password):
    """
    Memvalidasi format password.
    
    Fungsi ini memeriksa apakah password:
    1. Tidak kosong (truthy)
    2. Bertipe string
    3. Panjangnya minimal PASSWORD_MIN_LENGTH karakter
    
    Args:
        password (str): Password yang akan divalidasi
    
    Returns:
        bool: True jika password valid, False jika tidak valid
    """
    return bool(password and isinstance(password, str) and len(password) >= PASSWORD_MIN_LENGTH)