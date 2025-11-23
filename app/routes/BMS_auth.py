from flask import Blueprint, render_template, request, redirect, session
from app.database.BMS_db import BMS_db_connect
import hashlib

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ======================================
#  CEK APAKAH ADA USER DI DATABASE
# ======================================
def BMS_auth_has_users():
    """Mengembalikan True jika tabel users sudah ada penggunanya."""
    conn = BMS_db_connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM users")
    result = cur.fetchone()
    return result["total"] > 0


# ======================================
#  HASH & VERIFIKASI
# ======================================

def BMS_auth_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def BMS_auth_verify(username, password):
    conn = BMS_db_connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()

    if user and user["password"] == BMS_auth_hash(password):
        return user
    return None


# ======================================
#  ROLE CHECKER
# ======================================

def BMS_auth_is_root():
    return session.get("role") == "root"

def BMS_auth_is_admin():
    return session.get("role") == "admin"

def BMS_auth_is_member():
    return session.get("role") == "member"

def BMS_auth_is_login():
    return session.get("username") is not None


# ======================================
#  HALAMAN LOGIN
# ======================================

@auth.route("/login")
def BMS_auth_login_page():

    # Jika sudah login → arahkan sesuai role
    if BMS_auth_is_login():
        if BMS_auth_is_root() or BMS_auth_is_admin():
            return redirect("/admin/dashboard")
        return redirect("/user/home")

    return render_template("BMSauth_login.html")


@auth.route("/login-process", methods=["POST"])
def BMS_auth_login_process():
    username = request.form.get("username")
    password = request.form.get("password")

    user = BMS_auth_verify(username, password)

    if not user:
        return "Login gagal!"

    # Simpan ke session
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Redirect sesuai role
    if user["role"] == "root":
        return redirect("/admin/dashboard")

    if user["role"] == "admin":
        return redirect("/admin/dashboard")

    return redirect("/user/home")


# ======================================
#  HALAMAN REGISTER
# ======================================

@auth.route("/register")
def BMS_auth_register_page():
    return render_template("BMSauth_register.html")


@auth.route("/register-process", methods=["POST"])
def BMS_auth_register_process():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    conn = BMS_db_connect()
    cur = conn.cursor()

    # ======================================
    # CASE 1: Jika database masih kosong → buat ROOT pertama
    # ======================================
    if not BMS_auth_has_users():
        role = "root"  # override, paksa root pertama

        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, BMS_auth_hash(password), role)
        )
        conn.commit()

        return redirect("/auth/login")

    # ======================================
    # CASE 2: Database sudah ada user → hanya admin/member
    # ======================================
    if role == "root":
        return "Tidak boleh membuat root lagi!"

    if role not in ("admin", "member"):
        return "Role tidak valid!"

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