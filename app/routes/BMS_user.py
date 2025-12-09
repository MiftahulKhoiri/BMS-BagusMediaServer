import sqlite3
from flask import Blueprint, render_template, session, redirect
from app.BMS_config import DB_PATH
from .BMS_utils import require_login


user = Blueprint("user", __name__, url_prefix="/user")


# ======================================================
# DB Helper (simple)
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
# USER HOME PAGE
# ======================================================
@user.route("/home")
def BMS_user_home():
    # Proteksi login
    cek = require_login()
    if cek:
        return cek

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/auth/login")

    # Ambil data user
    conn = get_db()
    row = conn.execute(
        "SELECT id, username, role, nama, email, foto_profile, foto_background FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    # Jika user tidak ditemukan (DB mismatch)
    if not row:
        session.clear()
        return redirect("/auth/login")

    # Kirim data ke template BMSuser_home.html
    return render_template(
        "BMSuser_home.html",
        user=row
    )