from flask import Blueprint, render_template, request
from app.database.BMS_db import BMS_db_connect
import hashlib

register = Blueprint("register", __name__, url_prefix="/register")

# Halaman register
@register.route("/")
def BMS_register_page():
    return render_template("register_root.html")


# Proses register user baru
@register.route("/process", methods=["POST"])
def BMS_register_process():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")  # contoh: admin/member

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = BMS_db_connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_pw, role),
        )
        conn.commit()
        return "User berhasil dibuat!"
    except:
        return "Username sudah digunakan!"