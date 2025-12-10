import os
import sqlite3
import time
from flask import Blueprint, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.BMS_config import DB_PATH

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ======================================================
#   📌 Helper: DB Connection
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#   🛡 STORAGE FAILED LOGIN (Anti Brute Force)
# ======================================================
FAILED_ATTEMPTS = {}    # {username: {count: X, last: timestamp}}


MAX_ATTEMPT = 5         # gagal 5x
LOCK_TIME = 180         # dikunci 3 menit


def is_locked(username):
    """Cek apakah user sedang dikunci karena brute-force."""
    info = FAILED_ATTEMPTS.get(username)
    if not info:
        return False

    if info["count"] < MAX_ATTEMPT:
        return False

    # Masih dalam waktu penalti
    if time.time() - info["last"] < LOCK_TIME:
        return True

    # Reset lock expired
    FAILED_ATTEMPTS.pop(username, None)
    return False


def add_failed(username):
    """Tambahkan attempt gagal."""
    now = time.time()
    if username not in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[username] = {"count": 1, "last": now}
    else:
        FAILED_ATTEMPTS[username]["count"] += 1
        FAILED_ATTEMPTS[username]["last"] = now


# ======================================================
#   🛡 SESSION SECURITY
# ======================================================
def session_security():
    """Cek apakah session dicuri (IP/device berubah)."""
    if "user_id" not in session:
        return True

    ip = request.remote_addr
    agent = request.headers.get("User-Agent", "UNKNOWN")

    if session.get("ip") != ip or session.get("ua") != agent:
        session.clear()
        return False

    return True


# ======================================================
#   🔐 Helper Auth
# ======================================================
def BMS_auth_is_login():
    return "user_id" in session and session_security()


def BMS_auth_is_admin():
    return session.get("role") == "admin"


def BMS_auth_is_root():
    return session.get("role") == "root"


# ======================================================
#   🧾 REGISTER
# ======================================================
@auth.route("/register", methods=["GET", "POST"])
def BMS_auth_register():
    if request.method == "GET":
        return render_template("BMS_register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return {"success": False, "message": "Input tidak lengkap!"}, 400

    pw_hash = generate_password_hash(password)

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, pw_hash, "user")
        )
        conn.commit()
        conn.close()

        # LOG
        from app.routes.BMS_logger import BMS_write_log
        BMS_write_log("Registrasi akun baru", username)

    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username sudah digunakan!"}, 409

    return {"success": True, "message": "Registrasi berhasil!"}


# ======================================================
#   🔑 LOGIN
# ======================================================
@auth.route("/login", methods=["GET", "POST"])
def BMS_auth_login():
    if request.method == "GET":
        return render_template("BMS_login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    # Cek lock
    if is_locked(username):
        return {"success": False, "message": "Terlalu banyak gagal login. Coba lagi 3 menit."}, 429

    # Ambil user
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password"], password):
        add_failed(username)

        # LOG
        try:
            from app.routes.BMS_logger import BMS_write_error
            BMS_write_error("Login gagal (password salah?)", username)
        except:
            pass

        return {"success": False, "message": "Username atau password salah!"}, 401

    # Login sukses → reset brute-force
    FAILED_ATTEMPTS.pop(username, None)

    # Set session
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["ip"] = request.remote_addr
    session["ua"] = request.headers.get("User-Agent", "UNKNOWN")

    # LOG
    try:
        from app.routes.BMS_logger import BMS_write_log
        BMS_write_log("Login berhasil", username)
    except:
        pass

    return {
        "success": True,
        "redirect": "/admin/home" if user["role"] in ("admin", "root") else "/user/home"
    }


# ======================================================
#   🚪 LOGOUT
# ======================================================
@auth.route("/logout")
def BMS_auth_logout():
    username = session.get("username")

    try:
        from app.routes.BMS_logger import BMS_write_log
        BMS_write_log("Logout", username)
    except:
        pass

    session.clear()
    return render_template("BMS_welcome.html")


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