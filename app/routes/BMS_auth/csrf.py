import secrets
from flask import session

def ensure_csrf_token():
    """
    Memastikan session memiliki token CSRF.
    
    Fungsi ini mengecek apakah token CSRF sudah ada dalam session Flask.
    Jika belum ada, fungsi akan menghasilkan token acak sepanjang 16 byte 
    (dalam format URL-safe) dan menyimpannya di session.
    
    Returns:
        str: Token CSRF yang ada di session (baru dibuat atau sudah ada)
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return session["csrf_token"]

def verify_csrf(token_from_form):
    """
    Memverifikasi token CSRF dari form dengan token di session.
    
    Fungsi ini membandingkan token yang dikirim dari form dengan token
    yang tersimpan di session. Menggunakan compare_digest untuk menghindari
    timing attack jika tersedia, dengan fallback ke perbandingan biasa.
    
    Args:
        token_from_form (str): Token CSRF yang dikirim dari form request
    
    Returns:
        bool: True jika token valid, False jika tidak valid atau tidak ada
    """
    token = session.get("csrf_token")
    if not token or not token_from_form:
        return False

    try:
        from secrets import compare_digest
        # Menggunakan compare_digest untuk membandingkan string secara aman
        # terhadap timing attack
        return compare_digest(token, token_from_form)
    except Exception:
        # Fallback ke perbandingan biasa jika compare_digest tidak tersedia
        return token == token_from_form