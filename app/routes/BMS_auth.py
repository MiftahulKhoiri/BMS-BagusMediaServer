import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

# 🔗 Import DB_PATH dari config
from app.BMS_config import DB_PATH

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ======================================================
#   📌 Helper: Koneksi Database
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#   📌 Buat table user jika belum ada
# ======================================================
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    conn.commit()
    conn.close()


# Jalankan ketika blueprint di-load
init_db()


# ======================================================
#   🔐 Helper Auth Function
# ======================================================
def BMS_auth_is_login():
    return "user_id" in session


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
    role = request.form.get("role", "user").strip()

    if not username or not password:
        return "❌ Username & password tidak boleh kosong!", 400

    # Hash password
    pw_hash = generate_password_hash(password)

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, pw_hash, role)
        )
        conn.commit()

        try:
            from app.routes.BMS_logger import BMS_write_log
            BMS_write_log(f"Registrasi akun baru (role: {role})", username)
        except:
            pass

    except sqlite3.IntegrityError:
        conn.close()
        return "❌ Username sudah digunakan!", 409

    finally:
        conn.close()

    return redirect("/auth/login")


# ======================================================
#   🔑 LOGIN
# ======================================================
@auth.route("/login", methods=["GET", "POST"])
def BMS_auth_login():
    if request.method == "GET":
        return render_template("BMS_login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return "❌ Tidak boleh kosong!", 400

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()
    conn.close()

    if not user:
        return "❌ Username atau password salah!", 401

    # Cek hash password
    if not check_password_hash(user["password"], password):
        return "❌ Username atau password salah!", 401

    # Simpan sesi login
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Log aktivitas
    try:
        from app.routes.BMS_logger import BMS_write_log
        BMS_write_log("Login berhasil", user["username"])
    except:
        pass

    if user["role"] in ("root", "admin"):
        return redirect("/admin/home")

    return redirect("/user/home")


# ======================================================
#   🚪 LOGOUT
# ======================================================
@auth.route("/logout")
def BMS_auth_logout():
    username = session.get("username")
    if username:
        try:
            from app.routes.BMS_logger import BMS_write_log
            BMS_write_log("Logout", username)
        except:
            pass

    session.clear()
    return redirect("/auth/login")