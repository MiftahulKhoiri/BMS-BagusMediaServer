import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, session, jsonify
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
#   📌 Buat tabel user jika belum ada
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
    # GET → tampilkan halaman HTML
    if request.method == "GET":
        return render_template("BMS_register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = "user"  # Paksa semua akun baru menjadi user

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not username or not password:
        msg = "Username dan password harus diisi."
        if is_ajax:
            return jsonify({"status": "error", "message": msg})
        return render_template("BMS_register.html", error=msg)

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), role),
        )
        conn.commit()
        msg = "Registrasi berhasil!"
        if is_ajax:
            return jsonify({"status": "success", "message": msg})
        return redirect("/auth/login")
    except sqlite3.IntegrityError:
        msg = "Username sudah digunakan."
        if is_ajax:
            return jsonify({"status": "error", "message": msg})
        return render_template("BMS_register.html", error=msg)
    finally:
        conn.close()


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

    if not username or not password:
        msg = "Username dan password wajib diisi."
        if is_ajax:
            return jsonify({"status": "error", "message": msg})
        return render_template("BMS_login.html", error=msg)

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        msg = "Login berhasil."
        if is_ajax:
            return jsonify({"status": "success", "message": msg})
        return redirect("/")
    else:
        msg = "Username atau password salah."
        if is_ajax:
            return jsonify({"status": "error", "message": msg})
        return render_template("BMS_login.html", error=msg)


# ======================================================
#   🚪 LOGOUT
# ======================================================
@auth.route("/logout")
def BMS_auth_logout():
    session.clear()
    return redirect("/auth/login")


# ======================================================
#   🧩 INFO USER
# ======================================================
@auth.route("/me")
def BMS_auth_me():
    if not BMS_auth_is_login():
        return redirect("/auth/login")

    return jsonify(
        {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role"),
        }
    )