import os
import sqlite3
import time
import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, session, jsonify, current_app, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.BMS_config import DB_PATH

# Optional logger
try:
    from app.routes.BMS_logger import BMS_write
except Exception:
    def BMS_write(*args, **kwargs):
        pass

auth = Blueprint("auth", __name__, url_prefix="/auth")

# Config defaults
DEFAULT_LOCK_THRESHOLD = 5
DEFAULT_LOCK_WINDOW_MIN = 15
DEFAULT_COOLDOWN_MIN = 15
DEFAULT_SESSION_MINUTES = 60
PASSWORD_MIN_LENGTH = 8

# ======================================================
#   📌 DB Connection
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

# ======================================================
#   🔧 Ensure failed_login table
# ======================================================
def ensure_auth_tables():
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

ensure_auth_tables()

# ======================================================
#   🔍 Input validation
# ======================================================
_username_re = re.compile(r'^[A-Za-z0-9_]{3,32}$')

def valid_username(username):
    return bool(username and _username_re.match(username))

def valid_password(password):
    return bool(password and isinstance(password, str) and len(password) >= PASSWORD_MIN_LENGTH)

# ======================================================
#   🔍 CSRF
# ======================================================
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return session["csrf_token"]

def verify_csrf(token_from_form):
    token = session.get("csrf_token")
    return bool(token and token_from_form and secrets.compare_digest(token, token_from_form))

# ======================================================
#   🔍 Failed login tracking
# ======================================================
def add_failed_attempt(username, ip):
    conn = get_db()
    conn.execute("INSERT INTO failed_logins (username, ip, ts) VALUES (?, ?, ?)",
                 (username, ip, int(time.time())))
    conn.commit()
    conn.close()

def count_failed_attempts(username, ip, minutes_window):
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
    conn = get_db()
    conn.execute("DELETE FROM failed_logins WHERE username = ? OR ip = ?", (username, ip))
    conn.commit()
    conn.close()

# ======================================================
#   🔐 Lock check
# ======================================================
def is_locked(username, ip):
    threshold = current_app.config.get("BMS_LOCK_THRESHOLD", DEFAULT_LOCK_THRESHOLD)
    window = current_app.config.get("BMS_LOCK_WINDOW_MIN", DEFAULT_LOCK_WINDOW_MIN)
    attempts = count_failed_attempts(username, ip, window)
    return attempts >= threshold

# ======================================================
#   🔍 Session & Role check (FINAL FIXED)
# ======================================================
def BMS_auth_is_login():
    # HARUS ada user_id
    if not session.get("user_id"):
        return False

    # HARUS ada username
    if not session.get("username"):
        return False

    # Check expired
    expiry_ts = session.get("_expiry_ts")
    now = int(time.time())

    if not expiry_ts or now > int(expiry_ts):
        session.clear()
        return False

    return True

def BMS_auth_is_admin():
    return BMS_auth_is_login() and session.get("role") == "admin"

def BMS_auth_is_root():
    return BMS_auth_is_login() and session.get("role") == "root"

# ======================================================
#   🧾 REGISTER
# ======================================================
@auth.route("/register", methods=["GET", "POST"])
def register():
    ensure_csrf_token()

    if request.method == "GET":
        return render_template("BMS_register.html", csrf_token=session.get("csrf_token"))

    ip = request.remote_addr or "0.0.0.0"
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "")
    confirm = (request.form.get("confirm_password") or "")
    csrf_token = request.form.get("csrf_token")

    if not verify_csrf(csrf_token):
        flash("Permintaan tidak valid.", "error")
        return redirect(url_for("auth.register"))

    if not valid_username(username):
        flash("Username tidak valid (3–32 huruf/angka/_).", "error")
        return redirect(url_for("auth.register"))

    if not valid_password(password):
        flash(f"Password minimal {PASSWORD_MIN_LENGTH} karakter.", "error")
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
        except sqlite3.OperationalError:
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
#   🔐 LOGIN (FINAL FIXED)
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
        flash("Terlu banyak percobaan login. Coba lagi nanti.", "error")
        return redirect(url_for("auth.login"))

    # Ambil user
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

    # LOGIN BERHASIL
    clear_failed_attempts(username, ip)

    # ============ FIX UTAMA ============
    session.clear()
    session["user_id"] = user["id"]          # ⬅ WAJIB
    session["username"] = user["username"]
    session["role"] = user["role"]
    # ===================================

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
#   🔐 LOGOUT
# ======================================================
@auth.route("/logout")
def logout():
    session.clear()
    flash("Berhasil logout.", "info")
    return redirect(url_for("auth.login"))

# ======================================================
#   🔍 API ROLE
# ======================================================
@auth.route("/role")
def get_role():
    return jsonify({"role": session.get("role")})

# ======================================================
#   🔍 API CHECK SESSION VALID
# ======================================================
@auth.route("/valid")
def session_valid():
    return jsonify({"valid": BMS_auth_is_login()})