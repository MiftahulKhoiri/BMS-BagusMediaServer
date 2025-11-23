from flask import Blueprint, render_template, request
from app.database.BMS_db import BMS_db_connect
import hashlib

login = Blueprint("login", __name__, url_prefix="/login")

# Halaman login (root atau user)
@login.route("/")
def BMS_login_page():
    return render_template("login_root.html")


# Proses login
@login.route("/process", methods=["POST"])
def BMS_login_process():
    username = request.form.get("username")
    password = request.form.get("password")

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = BMS_db_connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()

    if user and user["password"] == hashed_pw:
        return f"Login Berhasil sebagai {user['role']}!"

    return "Login gagal!"