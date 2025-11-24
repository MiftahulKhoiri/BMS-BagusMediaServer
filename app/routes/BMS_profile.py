import sqlite3
from flask import Blueprint, render_template, request, redirect, session
from app.routes.BMS_auth import (
    BMS_auth_is_login
)

profile = Blueprint("profile", __name__, url_prefix="/profile")

DB_PATH = "/storage/emulated/0/BMS/database/users.db"


# ======================================================
#  📌 Helper Database
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#  🔐 Proteksi akses
# ======================================================
def BMS_profile_required():
    """User harus login untuk mengakses modul profil."""
    if not BMS_auth_is_login():
        return redirect("/auth/login")
    return None


# ======================================================
#  👤 Halaman Profil User
# ======================================================
@profile.route("/")
def BMS_profile_page():
    """
    Menampilkan file HTML:
    BMS_profile.html
    """
    check = BMS_profile_required()
    if check:
        return check

    return render_template("BMS_profile.html")


# ======================================================
#  ✏ Update Username
# ======================================================
@profile.route("/update_username", methods=["POST"])
def BMS_profile_update_username():
    check = BMS_profile_required()
    if check:
        return check

    new_username = request.form.get("username")

    if not new_username:
        return "❌ Username baru tidak boleh kosong!"

    user_id = session.get("user_id")

    conn = get_db()

    try:
        conn.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        conn.commit()
    except:
        conn.close()
        return "❌ Username sudah digunakan!"
    
    conn.close()

    session["username"] = new_username

    return "✔ Username berhasil diupdate!"


# ======================================================
#  🔐 Update Password
# ======================================================
@profile.route("/update_password", methods=["POST"])
def BMS_profile_update_password():
    check = BMS_profile_required()
    if check:
        return check

    old_pw = request.form.get("old")
    new_pw = request.form.get("new")

    if not old_pw or not new_pw:
        return "❌ Password tidak boleh kosong!"

    user_id = session.get("user_id")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    # cek password lama
    if user["password"] != old_pw:
        conn.close()
        return "❌ Password lama salah!"

    # update password baru
    conn.execute("UPDATE users SET password=? WHERE id=?", (new_pw, user_id))
    conn.commit()
    conn.close()

    return "✔ Password berhasil diupdate!"