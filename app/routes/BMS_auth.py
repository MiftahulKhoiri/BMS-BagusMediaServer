from flask import Blueprint, render_template, request, redirect, session
from app.database.BMS_db import BMS_db_connect
import hashlib

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ======================================
#  FUNGSI PEMBANTU
# ======================================

def BMS_auth_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def BMS_auth_verify(username, password):
    """Verifikasi user & password"""
    conn = BMS_db_connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()

    if user and user["password"] == BMS_auth_hash(password):
        return user
    return None


# ROLE CHECKER
def BMS_auth_is_root():
    return session.get("role") == "root"

def BMS_auth_is_admin():
    return session.get("role") == "admin"

def BMS_auth_is_member():
    return session.get("role") == "member"

def BMS_auth_is_login():
    return session.get("username") is not None


# ======================================
#  MIDDLEWARE PROTEKSI
# ======================================

def BMS_auth_require_login():
    if not BMS_auth_is_login():
        return redirect("/auth/login")

def BMS_auth_require_admin():
    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return "Akses ditolak!"

def BMS_auth_require_root():
    if not BMS_auth_is_root():
        return "Akses ditolak! Khusus ROOT!"


# ======================================
#  HALAMAN LOGIN
# ======================================

@auth.route("/login")
def BMS_auth_login_page():
    if BMS_auth_is_login():
        # Sudah login → langsung ke halaman masing-masing
        if BMS_auth_is_root() or BMS_auth_is_admin():
            return redirect("/admin/home")
        return redirect("/user/home")

    return render_template("BMSauth_login.html")


# PROSES LOGIN
@auth.route("/login-process", methods=["POST"])
def BMS_auth_login_process():
    username = request.form.get("username")
    password = request.form.get("password")

    user = BMS_auth_verify(username, password)

    if not user:
        return "Login gagal!"

    # Simpan session
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Redirect sesuai role
    if user["role"] == "root":
        return redirect("/admin/home")

    if user["role"] == "admin":
        return redirect("/admin/home")

    return redirect("/user/home")


# ======================================
#  HALAMAN REGISTER
# ======================================

@auth.route("/register")
def BMS_auth_register_page():
    return render_template("BMSauth_register.html")


# PROSES REGISTER
@auth.route("/register-process", methods=["POST"])
def BMS_auth_register_process():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    # Proteksi: user tidak boleh buat ROOT!
    if role == "root":
        return "Tidak boleh membuat root!"

    if role not in ("admin", "member"):
        return "Role tidak valid!"

    conn = BMS_db_connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, BMS_auth_hash(password), role)
        )
        conn.commit()
        return redirect("/auth/login")
    except:
        return "Username sudah dipakai!"


# ======================================
#  LOGOUT
# ======================================

@auth.route("/logout")
def BMS_auth_logout():
    session.clear()
    return redirect("/auth/login")