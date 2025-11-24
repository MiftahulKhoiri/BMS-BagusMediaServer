import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, session
from app.routes.BMS_logger import BMS_write_log

auth = Blueprint("auth", __name__, url_prefix="/auth")

# Lokasi database user
DB_PATH = "/storage/emulated/0/BMS/database/users.db"

# Pastikan folder database ada
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


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
            role TEXT
        )
    """)
    conn.commit()
    conn.close()

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

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role", "user")

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        conn.commit()
        BMS_write_log(f"Registrasi akun baru (role: {role})", username)

    except Exception:
        return "❌ Username sudah digunakan!"
    finally:
        conn.close()

    return "✔ Registrasi berhasil! <a href='/auth/login'>Login</a>"


# ======================================================
#   🔑 LOGIN
# ======================================================
@auth.route("/login", methods=["GET", "POST"])
def BMS_auth_login():
    if request.method == "GET":
        return render_template("BMS_login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()

    if not user:
        return "❌ Username atau password salah!"

    # Simpan sesi login
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Catat log
    BMS_write_log("Login berhasil", user["username"])

    # Arahkan sesuai role
    if user["role"] in ("root", "admin"):
        return redirect("/admin/dashboard")
    return redirect("/user/home")


# ======================================================
#   🚪 LOGOUT
# ======================================================
@auth.route("/logout")
def BMS_auth_logout():

    # Catat log sebelum session dihapus
    user = session.get("username")
    if user:
        BMS_write_log("Logout", user)

    session.clear()

    return redirect("/auth/login")