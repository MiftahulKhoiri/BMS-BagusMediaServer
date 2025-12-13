import time
import secrets
from flask import render_template, request, redirect, session, jsonify, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth
from .db import get_db
from .csrf import ensure_csrf_token, verify_csrf
from .validators import valid_username, valid_password
from .failed_logins import add_failed_attempt, is_locked, clear_failed_attempts
from .session_helpers import DEFAULT_SESSION_MINUTES, BMS_auth_is_login

# Optional logger - mencoba import logger dari aplikasi, jika gagal gunakan fungsi dummy
try:
    from app.routes.BMS_logger import BMS_write
except Exception:
    def BMS_write(*args, **kwargs):
        pass


# ======================================================
# REGISTER
# ======================================================
@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Menangani proses registrasi pengguna baru.
    
    Route ini mendukung dua metode:
    - GET: Menampilkan halaman registrasi
    - POST: Memproses data registrasi yang dikirimkan
    
    Validasi meliputi:
    1. Token CSRF
    2. Format username (alphanumeric dan underscore)
    3. Panjang password minimal
    4. Konfirmasi password cocok
    5. Username belum terdaftar
    
    Returns:
        JSON response (untuk AJAX) atau redirect dengan flash message (untuk form biasa)
    """
    # Pastikan token CSRF ada di session
    ensure_csrf_token()

    # Tampilkan form registrasi untuk request GET
    if request.method == "GET":
        return render_template("BMS_register.html", csrf_token=session.get("csrf_token"))

    # Ambil data dari form untuk request POST
    ip = request.remote_addr or "0.0.0.0"  # Alamat IP client
    username = (request.form.get("username") or "").strip()  # Username yang diinput
    password = request.form.get("password") or ""  # Password yang diinput
    confirm = request.form.get("confirm_password") or ""  # Konfirmasi password
    csrf_token = request.form.get("csrf_token")  # Token CSRF dari form

    # Validasi token CSRF
    if not verify_csrf(csrf_token):
        return _ajax_or_flash(
            field="username",
            message="Permintaan tidak valid.",
            redirect_url="auth.register"
        )

    # Validasi format username
    if not valid_username(username):
        return _ajax_or_flash(
            field="username",
            message="Username tidak valid (3–32 huruf/angka/_).",
            redirect_url="auth.register"
        )

    # Validasi panjang password
    if not valid_password(password):
        return _ajax_or_flash(
            field="password",
            message="Password minimal 8 karakter.",
            redirect_url="auth.register"
        )

    # Validasi konfirmasi password
    if password != confirm:
        return _ajax_or_flash(
            field="password",
            message="Konfirmasi password tidak cocok.",
            redirect_url="auth.register"
        )

    try:
        conn = get_db()
        cur = conn.cursor()

        # Cek apakah username sudah terdaftar
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return _ajax_or_flash(
                field="username",
                message="Username sudah digunakan!",
                redirect_url="auth.register"
            )

        # Generate hash password untuk disimpan
        pw_hash = generate_password_hash(password)

        # Coba insert dengan skema baru (password_hash), fallback ke skema lama (password)
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, pw_hash, "user")
            )
        except Exception:
            # Fallback untuk database lama yang menggunakan kolom 'password'
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, pw_hash, "user")
            )

        conn.commit()
        conn.close()

        # Registrasi berhasil
        return _ajax_or_flash(
    success=True,
    message="Registrasi berhasil! Akan otomatis pindah ke halaman login.",
    redirect_url="auth.login",      # untuk form biasa
    redirect_to="/auth/login"       # untuk AJAX
)

    except Exception as e:
        # Log error dan beri pesan umum ke user
        BMS_write(f"Register error: {e}")
        return _ajax_or_flash(
            field="username",
            message="Terjadi kesalahan pada server.",
            redirect_url="auth.register"
        )


# ======================================================
# LOGIN — HYBRID MODE (AJAX + Flash Support)
# ======================================================
@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Menangani proses login pengguna.
    
    Route ini mendukung dua metode:
    - GET: Menampilkan halaman login
    - POST: Memproses data login yang dikirimkan
    
    Proses validasi meliputi:
    1. Token CSRF
    2. Format username dan password
    3. Pengecekan penguncian akun (lockout)
    4. Verifikasi keberadaan user di database
    5. Verifikasi password
    
    Returns:
        JSON response (untuk AJAX) atau redirect dengan flash message (untuk form biasa)
    """
    # Pastikan token CSRF ada di session
    ensure_csrf_token()

    # Tampilkan form login untuk request GET
    if request.method == "GET":
        return render_template("BMS_login.html", csrf_token=session.get("csrf_token"))

    # Ambil data dari form untuk request POST
    ip = request.remote_addr or "0.0.0.0"  # Alamat IP client
    username = (request.form.get("username") or "").strip()  # Username yang diinput
    password = request.form.get("password") or ""  # Password yang diinput
    csrf_token = request.form.get("csrf_token")  # Token CSRF dari form

    # Validasi token CSRF
    if not verify_csrf(csrf_token):
        return _ajax_or_flash(
            field="username",
            message="Request tidak valid.",
            redirect_url="auth.login"
        )

    # Validasi format username
    if not valid_username(username):
        return _ajax_or_flash(
            field="username",
            message="Username tidak valid.",
            redirect_url="auth.login"
        )

    # Validasi panjang password
    if not valid_password(password):
        return _ajax_or_flash(
            field="password",
            message="Password minimal 8 karakter.",
            redirect_url="auth.login"
        )

    # Cek apakah akun/IP terkunci karena terlalu banyak percobaan gagal
    if is_locked(username, ip):
        return _ajax_or_flash(
            field="username",
            message="Terlalu banyak percobaan login. Coba lagi nanti.",
            redirect_url="auth.login"
        )

    # Ambil data user dari database
    conn = get_db()
    cur = conn.cursor()
    # Query dengan support untuk kedua skema password (lama dan baru)
    cur.execute("""
        SELECT id, username, role,
               password_hash AS newpass,
               password AS oldpass
        FROM users
        WHERE username = ?
    """, (username,))
    user = cur.fetchone()
    conn.close()

    # Jika user tidak ditemukan
    if not user:
        add_failed_attempt(username, ip)  # Catat percobaan gagal
        return _ajax_or_flash(
            field="username",
            message="Username tidak terdaftar.",
            redirect_url="auth.login"
        )

    # Ambil hash password dari kolom baru (password_hash) atau lama (password)
    stored_hash = user["newpass"] or user["oldpass"]

    # Verifikasi password
    if not check_password_hash(stored_hash, password):
        add_failed_attempt(username, ip)  # Catat percobaan gagal
        return _ajax_or_flash(
            field="password",
            message="Password salah.",
            redirect_url="auth.login"
        )

    # Login berhasil, hapus riwayat percobaan gagal
    clear_failed_attempts(username, ip)

    # Bersihkan session lama dan buat session baru
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Set expiry time untuk session
    expiry = int(time.time()) + (DEFAULT_SESSION_MINUTES * 60)
    session["_expiry_ts"] = expiry
    session.permanent = True  # Gunakan permanent session Flask

    # Generate token CSRF baru untuk session ini
    session["csrf_token"] = secrets.token_urlsafe(16)

    # Tentukan redirect URL berdasarkan role user
    redirect_url = "/admin/home" if user["role"] in ("admin", "root") else "/user/home"

    # Response JSON untuk AJAX
    return jsonify({
        "success": True,
        "redirect": redirect_url
    })


# ======================================================
# Logout
# ======================================================
@auth.route("/logout")
def logout():
    """
    Menangani proses logout pengguna.
    
    Fungsi ini menghapus semua data dari session dan
    mengarahkan user kembali ke halaman login.
    
    Returns:
        Redirect ke halaman login dengan flash message
    """
    session.clear()  # Hapus semua data session
    flash("Berhasil logout.", "info")
    return redirect(url_for("auth.login"))


# ======================================================
# API Role
# ======================================================
@auth.route("/role")
def get_role():
    """
    Mengembalikan role user saat ini dalam format JSON.
    
    Endpoint ini berguna untuk client-side JavaScript
    yang perlu mengetahui role user tanpa reload halaman.
    
    Returns:
        JSON object dengan key 'role' yang berisi role user
    """
    return jsonify({"role": session.get("role")})


# ======================================================
# API Check Session Valid
# ======================================================
@auth.route("/valid")
def session_valid():
    """
    Mengecek validitas session saat ini.
    
    Endpoint ini mengembalikan status apakah user
    sedang login dengan session yang valid.
    
    Returns:
        JSON object dengan key 'valid' (boolean)
    """
    return jsonify({"valid": BMS_auth_is_login()})


# ======================================================
# HELPER: HYBRID RESPONSE (AJAX / FLASH)
# ======================================================
def _ajax_or_flash(field=None, message="", redirect_url=None, success=False, redirect_to=None):
    """
    Helper function untuk memberikan response hybrid (AJAX/non-AJAX).
    
    Fungsi ini mendeteksi apakah request berasal dari AJAX (berdasarkan header)
    dan memberikan response yang sesuai:
    - Untuk AJAX: Mengembalikan JSON dengan informasi error/success
    - Untuk non-AJAX: Menggunakan flash messages dan redirect
    
    Args:
        field (str, optional): Field form yang menyebabkan error
        message (str): Pesan yang akan ditampilkan
        redirect_url (str): Endpoint Flask untuk redirect (non-AJAX)
        success (bool): Status keberhasilan
        redirect_to (str): URL untuk redirect (AJAX)
    
    Returns:
        JSON response (untuk AJAX) atau redirect (untuk non-AJAX)
    """
    # Deteksi apakah request berasal dari AJAX
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # ========================================================
    # MODE AJAX (JSON RESPONSE)
    # ========================================================
    if is_ajax:
        return jsonify({
            "success": success,
            "error_field": field,
            "message": message,
            "redirect": redirect_to
        })

    # ========================================================
    # MODE BROWSER NORMAL (FLASH + REDIRECT)
    # ========================================================
    # Tentukan kategori flash message berdasarkan status success
    flash(message, "error" if not success else "success")

    # Default redirect ke halaman login jika tidak ada redirect_url
    if not redirect_url:
        redirect_url = "auth.login"

    # Redirect ke endpoint yang ditentukan
    return redirect(url_for(redirect_url))