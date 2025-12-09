import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.BMS_config import DB_PATH

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ======================================================
#   📌 Helper: Koneksi Database
# ======================================================
def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print("DB Error:", e)
        raise


# ======================================================
#   📌 Buat table user jika belum ada
#   Dipanggil HANYA sekali ketika server dijalankan
# ======================================================
def init_db():
    try:
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("[INIT_DB ERROR]", e)


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
    role = "user"

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # Validasi input
    if not username or not password:
        msg = {"success": False, "message": "Username & password wajib diisi!"}
        return (msg, 400) if is_ajax else ("❌ Username & password wajib diisi!", 400)

    pw_hash = generate_password_hash(password)

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, pw_hash, role)
        )
        conn.commit()
        conn.close()

        # Log
        try:
            from app.routes.BMS_logger import BMS_write_log
            BMS_write_log(f"Registrasi akun baru", username)
        except:
            pass

    except sqlite3.IntegrityError:
        msg = {"success": False, "message": "Username sudah digunakan!"}
        return (msg, 409) if is_ajax else ("❌ Username sudah digunakan!", 409)

    if is_ajax:
        return {"success": True, "message": "Registrasi berhasil!"}

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

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # Validasi input
    if not username or not password:
        msg = {
            "success": False,
            "message": "Input tidak lengkap!",
            "errors": {
                "username": "Username kosong!" if not username else None,
                "password": "Password kosong!" if not password else None
            }
        }
        return (msg, 400) if is_ajax else ("❌ Input tidak lengkap!", 400)

    try:
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": "DB error", "detail": str(e)}), 500

    # Cek user & password
    if not user or not check_password_hash(user["password"], password):
        msg = {
            "success": False,
            "message": "Username atau password salah!",
            "errors": {"password": "Password salah!"}
        }
        return (msg, 401) if is_ajax else ("❌ Username atau password salah!", 401)

    # Login sukses
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    # Log
    try:
        from app.routes.BMS_logger import BMS_write_log
        BMS_write_log("Login berhasil", user["username"])
    except:
        pass

    redirect_url = "/admin/home" if user["role"] in ("admin", "root") else "/user/home"

    if is_ajax:
        return {"success": True, "message": "Login berhasil!", "redirect": redirect_url}

    return redirect(redirect_url)


# ======================================================
#   🚪 LOGOUT
# ======================================================
@auth.route("/logout")
def BMS_auth_logout():
    username = session.get("username")

    try:
        from app.routes.BMS_logger import BMS_write_log
        if username:
            BMS_write_log("Logout", username)
    except:
        pass

    session.clear()
    return render_template("BMS_welcome.html")


# ======================================================
#   🔍 GET ROLE (API)
# ======================================================
@auth.route("/role")
def get_role():
    return jsonify({"role": session.get("role")})