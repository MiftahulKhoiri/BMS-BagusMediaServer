import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.utils import secure_filename

# 🔗 Import config pusat (path sinkron)
from app.BMS_config import DB_PATH, PROFILE_FOLDER

# 🔐 Import login check
from app.routes.BMS_auth import BMS_auth_is_login


# ======================================================
#  🔧 Blueprint
# ======================================================
profile = Blueprint("profile", __name__, url_prefix="/profile")


# ======================================================
#  📌 Pastikan folder profile ada
# ======================================================
os.makedirs(PROFILE_FOLDER, exist_ok=True)


# ======================================================
#  📌 DB Helper
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#  🔐 Proteksi Halaman
# ======================================================
def BMS_profile_required():
    if not BMS_auth_is_login():
        return redirect("/auth/login")
    return None


# ======================================================
#  👤 Halaman Profil
# ======================================================
@profile.route("/")
def BMS_profile_page():
    check = BMS_profile_required()
    if check:
        return check

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?", (session.get("user_id"),)
    ).fetchone()
    conn.close()

    return render_template("BMS_profile.html", user=user)


# ======================================================
#  ✏ Halaman Edit Profil
# ======================================================
@profile.route("/edit")
def BMS_profile_edit_page():
    check = BMS_profile_required()
    if check:
        return check

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?", (session.get("user_id"),)
    ).fetchone()
    conn.close()

    return render_template("BMS_edit_profile.html", user=user)


# ======================================================
#  💾 SIMPAN PROFIL
# ======================================================
@profile.route("/save", methods=["POST"])
def BMS_profile_save():
    check = BMS_profile_required()
    if check:
        return check

    user_id = session.get("user_id")

    # Data form
    nama = request.form.get("nama")
    umur = request.form.get("umur")
    gender = request.form.get("gender")
    email = request.form.get("email")
    bio = request.form.get("bio")

    # =======================
    # Upload Foto Profil
    # =======================
    foto_profile_path = None
    foto_profile = request.files.get("foto_profile")

    if foto_profile and foto_profile.filename != "":
        filename = f"profile_{user_id}_" + secure_filename(foto_profile.filename)
        foto_profile_path = os.path.join(PROFILE_FOLDER, filename)
        foto_profile.save(foto_profile_path)

    # =======================
    # Upload Foto Background
    # =======================
    foto_background_path = None
    foto_background = request.files.get("foto_background")

    if foto_background and foto_background.filename != "":
        filename = f"background_{user_id}_" + secure_filename(foto_background.filename)
        foto_background_path = os.path.join(PROFILE_FOLDER, filename)
        foto_background.save(foto_background_path)

    # =======================
    # Update Database
    # =======================
    conn = get_db()

    update_fields = {
        "nama": nama,
        "umur": umur,
        "gender": gender,
        "email": email,
        "bio": bio
    }

    if foto_profile_path:
        update_fields["foto_profile"] = foto_profile_path

    if foto_background_path:
        update_fields["foto_background"] = foto_background_path

    set_query = ", ".join([f"{k}=?" for k in update_fields.keys()])
    values = list(update_fields.values())
    values.append(user_id)

    conn.execute(f"UPDATE users SET {set_query} WHERE id=?", values)
    conn.commit()
    conn.close()

    # =======================
    # Update session real-time
    # =======================
    if nama:
        session["nama"] = nama
    if foto_profile_path:
        session["foto_profile"] = foto_profile_path
    if foto_background_path:
        session["foto_background"] = foto_background_path

    # =======================
    # Redirect sesuai role
    # =======================
    role = session.get("role")

    if role in ("admin", "root"):
        return redirect("/admin/home")
    return redirect("/user/home")