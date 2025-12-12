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

    if not verify_csrf(csrf_token):
        flash("Permintaan tidak valid.", "error")
        return redirect(url_for("auth.register"))

    if not valid_username(username):
        flash("Username tidak valid (3–32 huruf/angka/_).", "error")
        return redirect(url_for("auth.register"))

    if not valid_password(password):
        flash("Password minimal 8 karakter.", "error")
        return redirect(url_for("auth.register"))

    if password != confirm:
        flash("Konfirmasi password tidak cocok.", "error")
        return redirect(url_for("auth.register"))

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            flash("Username sudah digunakan!", "error")
            return redirect(url_for("auth.register"))

        pw_hash = generate_password_hash(password)

        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, pw_hash, "user")
            )
        except Exception:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, pw_hash, "user")
            )

        conn.commit()
        conn.close()

        flash("Registrasi berhasil!", "success")
        return redirect(url_for("auth.login"))

    except Exception as e:
        BMS_write(f"Register error: {e}")
        flash("Terjadi kesalahan pada server.", "error")
        return redirect(url_for("auth.register"))

# ======================================================
# LOGIN
# ======================================================
@auth.route("/login", methods=["GET", "POST"])
def login():
    ensure_csrf_token()

    if request.method == "GET":
        return render_template("BMS_login.html", csrf_token=session.get("csrf_token"))

    ip = request.remote_addr or "0.0.0.0"
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    csrf_token = request.form.get("csrf_token")

    if not verify_csrf(csrf_token):
        flash("Invalid request.", "error")
        return redirect(url_for("auth.login"))

    if not valid_username(username) or not valid_password(password):
        add_failed_attempt(username, ip)
        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    if is_locked(username, ip):
        flash("Terlalu banyak percobaan login. Coba lagi nanti.", "error")
        return redirect(url_for("auth.login"))

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

    if not user:
        add_failed_attempt(username, ip)
        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    stored_hash = user["newpass"] or user["oldpass"]

    if not check_password_hash(stored_hash, password):
        add_failed_attempt(username, ip)
        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    clear_failed_attempts(username, ip)

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    expiry = int(time.time()) + (DEFAULT_SESSION_MINUTES * 60)
    session["_expiry_ts"] = expiry
    session.permanent = True
    session["csrf_token"] = secrets.token_urlsafe(16)

    flash("Login berhasil!", "success")

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