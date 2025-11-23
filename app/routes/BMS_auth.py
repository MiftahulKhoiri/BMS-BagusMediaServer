from flask import Blueprint, render_template, request, redirect, session
from app.database.BMS_db import BMS_db_connect
import hashlib

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ===============================
#  FUNGSI PEMBANTU
# ===============================

def BMS_auth_hash(password):
    """Hash password dengan SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def BMS_auth_verify(username, password):
    """Verifikasi username & password"""
    conn = BMS_db_connect()
    cur = conn.cursor()

    hashed_pw = BMS_auth_hash(password)

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()

    if user and user["password"] == hashed_pw:
        return user

    return None


def BMS_auth_is_root():
    """Cek apakah user login sebagai root"""
    return session.get("role") == "root"


def BMS_auth_is_admin():
    """Cek apakah user login sebagai admin"""
    return session.get("role") == "admin"


def BMS_auth_is_member():
    """Cek apakah user login sebagai member"""
    return session.get("role") == "member"



# ===============================
#  HALAMAN LOGIN
# ===============================

@auth.route("/login")
def BMS_auth_login_page():
    return render_template("auth_login.html")


# PROSES LOGIN
@auth.route("/login-process", methods=["POST"])
def BMS_auth_login_process():
    username = request.form.get("username")
    password = request.form.get("password")

    user = BMS_auth_verify(username, password)

    if user:
        session["username"] = user["username"]
        session["role"] = user["role"]
        return f"Login berhasil! Role: {user['role']}"
    else:
        return "Login gagal!"


# ===============================
#  HALAMAN REGISTER
# ===============================

@auth.route("/register")
def BMS_auth_register_page():
    return render_template("auth_register.html")


# PROSES REGISTER
@auth.route("/register-process", methods=["POST"])
def BMS_auth_register_process():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")  # root/admin/member

    hashed_pw = BMS_auth_hash(password)

    conn = BMS_db_connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_pw, role)
        )
        conn.commit()

        return "Akun berhasil dibuat!"
    except:
        return "Username sudah digunakan!"


# ===============================
#  LOGOUT
# ===============================

@auth.route("/logout")
def BMS_auth_logout():
    session.clear()
    return "Anda telah logout."