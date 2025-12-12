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

# Optional logger
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
    ensure_csrf_token()

    if request.method == "GET":
        return render_template("BMS_register.html", csrf_token=session.get("csrf_token"))

    ip = request.remote_addr or "0.0.0.0"
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""
    csrf_token = request.form.get("csrf_token")

    # CSRF
    if not verify_csrf(csrf_token):
        return _ajax_or_flash(
            field="username",
            message="Permintaan tidak valid.",
            redirect_url="auth.register"
        )

    # VALIDASI USERNAME
    if not valid_username(username):
        return _ajax_or_flash(
            field="username",
            message="Username tidak valid (3–32 huruf/angka/_).",
            redirect_url="auth.register"
        )

    # VALIDASI PASSWORD
    if not valid_password(password):
        return _ajax_or_flash(
            field="password",
            message="Password minimal 8 karakter.",
            redirect_url="auth.register"
        )

    if password != confirm:
        return _ajax_or_flash(
            field="password",
            message="Konfirmasi password tidak cocok.",
            redirect_url="auth.register"
        )

    try:
        conn = get_db()
        cur = conn.cursor()

        # Apakah username sudah ada?
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return _ajax_or_flash(
                field="username",
                message="Username sudah digunakan!",
                redirect_url="auth.register"
            )

        pw_hash = generate_password_hash(password)

        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, pw_hash, "user")
            )
        except Exception:
            # fallback DB lama
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, pw_hash, "user")
            )

        conn.commit()
        conn.close()

        return _ajax_or_flash(
            success=True,
            redirect="/auth/login",
            message="Registrasi berhasil!"
        )

    except Exception as e:
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
    ensure_csrf_token()

    # Tampilkan halaman login
    if request.method == "GET":
        return render_template("BMS_login.html", csrf_token=session.get("csrf_token"))

    ip = request.remote_addr or "0.0.0.0"
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    csrf_token = request.form.get("csrf_token")

    # CSRF CHECK
    if not verify_csrf(csrf_token):
        return _ajax_or_flash(
            field="username",
            message="Request tidak valid.",
            redirect_url="auth.login"
        )

    # VALIDASI FORM DASAR
    if not valid_username(username):
        return _ajax_or_flash(
            field="username",
            message="Username tidak valid.",
            redirect_url="auth.login"
        )

    if not valid_password(password):
        return _ajax_or_flash(
            field="password",
            message="Password minimal 8 karakter.",
            redirect_url="auth.login"
        )

    # CEK LOCKOUT
    if is_locked(username, ip):
        return _ajax_or_flash(
            field="username",
            message="Terlalu banyak percobaan login. Coba lagi nanti.",
            redirect_url="auth.login"
        )

    # AMBIL DATA USER
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, role,
               password_hash AS newpass,
               password AS oldpass
        FROM users
        WHERE username = ?
    """, (username,))
    user = cur.fetchone()
    conn.close()

    # USER TIDAK ADA
    if not user:
        add_failed_attempt(username, ip)
        return _ajax_or_flash(
            field="username",
            message="Username tidak terdaftar.",
            redirect_url="auth.login"
        )

    stored_hash = user["newpass"] or user["oldpass"]

    # PASSWORD SALAH
    if not check_password_hash(stored_hash, password):
        add_failed_attempt(username, ip)
        return _ajax_or_flash(
            field="password",
            message="Password salah.",
            redirect_url="auth.login"
        )

    # LOGIN SUKSES
    clear_failed_attempts(username, ip)

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    expiry = int(time.time()) + (DEFAULT_SESSION_MINUTES * 60)
    session["_expiry_ts"] = expiry
    session.permanent = True

    session["csrf_token"] = secrets.token_urlsafe(16)

    redirect_url = "/admin/home" if user["role"] in ("admin", "root") else "/user/home"

    return jsonify({
        "success": True,
        "redirect": redirect_url
    })


# ======================================================
# Logout
# ======================================================
@auth.route("/logout")
def logout():
    session.clear()
    flash("Berhasil logout.", "info")
    return redirect(url_for("auth.login"))


# ======================================================
# API Role
# ======================================================
@auth.route("/role")
def get_role():
    return jsonify({"role": session.get("role")})


# ======================================================
# API Check Session Valid
# ======================================================
@auth.route("/valid")
def session_valid():
    return jsonify({"valid": BMS_auth_is_login()})


# ======================================================
# HELPER: HYBRID RESPONSE (AJAX / FLASH)
# ======================================================
def _ajax_or_flash(field=None, message="", redirect_url=None, success=False, redirect=None):
    """
    Jika request dari AJAX (fetch) → kirim JSON error
    Jika request biasa → gunakan flash + redirect
    """
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Mode AJAX
        return jsonify({
            "success": success,
            "error_field": field,
            "message": message,
            "redirect": redirect
        })

    # Mode normal (browser biasa)
    flash(message, "error" if not success else "success")
    return redirect(url_for(redirect_url)) if redirect_url else redirect