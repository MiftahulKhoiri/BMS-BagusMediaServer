import os
import sqlite3
import time
import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, session, jsonify, current_app, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.BMS_config import DB_PATH

# Optional logger from your project (if exists)
try:
    from app.routes.BMS_logger import BMS_write
except Exception:
    def BMS_write(*args, **kwargs):
        # fallback no-op logger to avoid crashes if logger not available
        pass

auth = Blueprint("auth", __name__, url_prefix="/auth")

# Configuration defaults (can be overridden from app config)
DEFAULT_LOCK_THRESHOLD = 5       # failed attempts
DEFAULT_LOCK_WINDOW_MIN = 15     # minutes window to count failed attempts
DEFAULT_COOLDOWN_MIN = 15        # lockout duration in minutes
DEFAULT_SESSION_MINUTES = 60     # session lifetime in minutes
PASSWORD_MIN_LENGTH = 8

# ======================================================
#   📌 Helper: DB Connection
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

# ======================================================
#   🔧 Ensure required tables exist for auth safety
# ======================================================
def ensure_auth_tables():
    conn = get_db()
    cur = conn.cursor()
    # users table is expected to exist already; add failed_logins if missing
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
#   🔍 Input validation helpers
# ======================================================
_username_re = re.compile(r'^[A-Za-z0-9_]{3,32}$')

def valid_username(username):
    return bool(username and _username_re.match(username))

def valid_password(password):
    return bool(password and isinstance(password, str) and len(password) >= PASSWORD_MIN_LENGTH)

# ======================================================
#   🔍 CSRF helpers (simple token approach)
# ======================================================
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return session["csrf_token"]

def verify_csrf(token_from_form):
    token = session.get("csrf_token")
    return bool(token and token_from_form and secrets.compare_digest(token, token_from_form))

# ======================================================
#   🔍 Failed login tracking (stored in DB)
# ======================================================
def add_failed_attempt(username, ip):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO failed_logins (username, ip, ts) VALUES (?, ?, ?)", (username, ip, int(time.time())))
        conn.commit()
    finally:
        conn.close()

def count_failed_attempts(username, ip, minutes_window):
    cutoff = int(time.time()) - (minutes_window * 60)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM failed_logins WHERE (username = ? OR ip = ?) AND ts >= ?", (username, ip, cutoff))
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0

def clear_failed_attempts(username, ip):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM failed_logins WHERE username = ? OR ip = ?", (username, ip))
    conn.commit()
    conn.close()

# ======================================================
#   🔐 Lock check
# ======================================================
def is_locked(username, ip):
    # Use app config overrides if provided
    threshold = current_app.config.get("BMS_LOCK_THRESHOLD", DEFAULT_LOCK_THRESHOLD)
    window = current_app.config.get("BMS_LOCK_WINDOW_MIN", DEFAULT_LOCK_WINDOW_MIN)
    attempts = count_failed_attempts(username, ip, window)
    return attempts >= threshold

# ======================================================
#   🔍 Session & Role check
# ======================================================
def BMS_auth_is_login():
    username = session.get("username")
    if not username:
        return False
    expiry_ts = session.get("_expiry_ts")
    if not expiry_ts or int(time.time()) > int(expiry_ts):
        # session expired
        session.clear()
        return False
    return True

def BMS_auth_is_admin():
    return BMS_auth_is_login() and session.get("role") == "admin"

def BMS_auth_is_root():
    return BMS_auth_is_login() and session.get("role") == "root"

# ======================================================
#   🧾 REGISTER (GET -> show form, POST -> create user -> redirect + flash)
# ======================================================
@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Register new user.
    Uses standard POST -> redirect -> flash flow (not JSON).
    """
    ensure_csrf_token()

    if request.method == "GET":
        return render_template("BMS_register.html", csrf_token=session.get("csrf_token"))

    # POST -> process registration
    ip = request.remote_addr or "0.0.0.0"
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "")
    confirm = (request.form.get("confirm_password") or "")

    # Basic CSRF verification
    csrf_token = request.form.get("csrf_token")
    if not verify_csrf(csrf_token):
        BMS_write(f"CSRF mismatch on register attempt from {ip}")
        flash("Permintaan tidak valid.", "error")
        return redirect(url_for("auth.register"))

    # Validation
    if not valid_username(username):
        BMS_write(f"Register failed - invalid username format from {ip}: {username}")
        flash("Username tidak valid. Gunakan huruf, angka atau underscore (3-32 karakter).", "error")
        return redirect(url_for("auth.register"))

    if not valid_password(password):
        BMS_write(f"Register failed - weak password from {ip} username={username}")
        flash(f"Password minimal {PASSWORD_MIN_LENGTH} karakter.", "error")
        return redirect(url_for("auth.register"))

    # Confirm password if provided
    if confirm and password != confirm:
        BMS_write(f"Register failed - password mismatch from {ip} username={username}")
        flash("Konfirmasi password tidak cocok.", "error")
        return redirect(url_for("auth.register"))

    # Check for existing username
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cur.fetchone()
        if existing:
            conn.close()
            BMS_write(f"Register failed - username taken: {username} from {ip}")
            flash("Username sudah digunakan.", "error")
            return redirect(url_for("auth.register"))

        # Insert new user - prefer column name 'password_hash', handle legacy 'password' column
        pw_hash = generate_password_hash(password)

        # Try insert with password_hash column first
        try:
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                        (username, pw_hash, "user"))
        except sqlite3.OperationalError:
            # Fallback if table has column named 'password' instead
            cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (username, pw_hash, "user"))

        conn.commit()
        conn.close()

        # Log registration
        try:
            BMS_write(f"New user registered: {username} from {ip}")
        except Exception:
            pass

        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("auth.login"))

    except sqlite3.IntegrityError:
        # Unique constraint violation
        BMS_write(f"Register IntegrityError - username taken: {username} from {ip}")
        flash("Username sudah digunakan.", "error")
        return redirect(url_for("auth.register"))
    except Exception as e:
        # Generic error
        try:
            BMS_write(f"Register error for {username} from {ip}: {e}")
        except Exception:
            pass
        flash("Terjadi kesalahan saat registrasi. Coba lagi nanti.", "error")
        return redirect(url_for("auth.register"))

# ======================================================
#   🔍 Route: Login (GET shows form + CSRF token, POST verifies)
# ======================================================
@auth.route("/login", methods=["GET", "POST"])
def login():
    ensure_csrf_token()
    if request.method == "GET":
        # Provide csrf token via session for templates to consume
        return render_template("BMS_login.html", csrf_token=session.get("csrf_token"))

    # POST -> authenticate
    ip = request.remote_addr or "0.0.0.0"
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    csrf_token = request.form.get("csrf_token")

    # Basic CSRF & input validation
    if not verify_csrf(csrf_token):
        BMS_write(f"CSRF token mismatch on login attempt from {ip}")
        flash("Invalid request.", "error")
        return redirect(url_for("auth.login"))

    if not valid_username(username) or not valid_password(password):
        add_failed_attempt(username, ip)
        BMS_write(f"Invalid credentials format from {ip} username={username}")
        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    # Lock check
    if is_locked(username, ip):
        BMS_write(f"Locked out login attempt from {ip} for username={username}")
        flash("Too many failed attempts. Try again later.", "error")
        return redirect(url_for("auth.login"))

    # Fetch user securely using parameterized queries
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if not user:
        add_failed_attempt(username, ip)
        BMS_write(f"Failed login - user not found: {username} from {ip}")
        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    # Verify password
    stored_hash = user["password_hash"] if "password_hash" in user.keys() else user.get("password")
    if not stored_hash or not check_password_hash(stored_hash, password):
        add_failed_attempt(username, ip)
        BMS_write(f"Failed login - bad password: {username} from {ip}")
        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    # Successful login: clear failed attempts, set session with expiry and regenerate token
    clear_failed_attempts(username, ip)

    # Regenerate session by clearing and creating new session values
    session.clear()
    session["username"] = user["username"]
    session["role"] = user["role"] if "role" in user.keys() else "user"
    # session expiry timestamp (unix)
    lifetime_minutes = current_app.config.get("PERMANENT_SESSION_LIFETIME_MINUTES", DEFAULT_SESSION_MINUTES)
    expiry = int(time.time()) + (int(lifetime_minutes) * 60)
    session["_expiry_ts"] = expiry
    session.permanent = True
    # rotate csrf token after login
    session["csrf_token"] = secrets.token_urlsafe(16)

    BMS_write(f"User logged in: {username} from {ip}")
    flash("Login successful.", "success")
    return redirect(url_for("profile.user_home") if session.get("role") != "admin" else url_for("admin.admin_home"))

# ======================================================
#   🔍 Route: Logout
# ======================================================
@auth.route("/logout")
def logout():
    username = session.get("username")
    ip = request.remote_addr or "0.0.0.0"
    session.clear()
    BMS_write(f"User logged out: {username} from {ip}")
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))

# ======================================================
#   🔍 API GET ROLE
# ======================================================
@auth.route("/role")
def get_role():
    return jsonify({"role": session.get("role")})

# ======================================================
#   🔍 API CHECK SESSION VALID
# ======================================================
@auth.route("/valid")
def session_valid():
    """Frontend bisa pakai ini untuk cek apakah session masih valid."""
    return jsonify({"valid": BMS_auth_is_login()})