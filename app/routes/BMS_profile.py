import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, session, send_from_directory, abort
from werkzeug.utils import secure_filename

from app.BMS_config import PICTURES_FOLDER,DB_PATH
from app.routes.BMS_auth.session_helpers import BMS_auth_is_login

profile = Blueprint("profile", __name__, url_prefix="/profile")

# Folder khusus foto profile
PROFILE_FOLDER = os.path.join(PICTURES_FOLDER, "profile")
PROFILE_BACKGROUND_FOLDER = os.path.join(PICTURES_FOLDER, "profile_background")

# Pastikan folder ada
os.makedirs(PROFILE_FOLDER, exist_ok=True)
os.makedirs(PROFILE_BACKGROUND_FOLDER, exist_ok=True)

# ======================================================
#  DB Helper
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#  Proteksi Halaman (Aman)
# ======================================================
def BMS_profile_required():
    if not BMS_auth_is_login():
        return redirect("/auth/login")

    # Pastikan session user_id ada
    if not session.get("user_id"):
        return redirect("/auth/login")

    return None


# ======================================================
#  Validasi Ekstensi Aman
# ======================================================
ALLOWED_IMG = {"jpg", "jpeg", "png", "gif", "webp"}

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMG


# ======================================================
#  Load Image
# ======================================================
@profile.route("/image/<filename>")
def BMS_profile_image(filename):
    filename = secure_filename(filename)  # Anti traversal
    return send_from_directory(PROFILE_FOLDER, filename)

@profile.route("/background/<filename>")
def BMS_profile_background(filename):
    filename = secure_filename(filename)
    return send_from_directory(PROFILE_BACKGROUND_FOLDER, filename)


# ======================================================
#  Halaman Profil
# ======================================================
@profile.route("/")
def BMS_profile_page():
    cek = BMS_profile_required()
    if cek:
        return cek

    user_id = session.get("user_id")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    # Jika user tidak ditemukan, logout otomatis
    if not user:
        session.clear()
        return redirect("/auth/login")

    return render_template("BMS_profile.html", user=user)


# ======================================================
#  Halaman Edit Profil
# ======================================================
@profile.route("/edit")
def BMS_profile_edit_page():
    cek = BMS_profile_required()
    if cek:
        return cek

    user_id = session.get("user_id")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    if not user:
        session.clear()
        return redirect("/auth/login")

    return render_template("BMS_edit_profile.html", user=user)


# ======================================================
#  SIMPAN PROFIL — Versi Aman
# ======================================================
@profile.route("/save", methods=["POST"])
def BMS_profile_save():
    cek = BMS_profile_required()
    if cek:
        return cek

    user_id = session.get("user_id")

    # Ambil data input
    nama = request.form.get("nama", "")
    umur = request.form.get("umur", "")
    gender = request.form.get("gender", "")
    email = request.form.get("email", "")
    bio = request.form.get("bio", "")

    # Ambil user lama (cek foto)
    conn = get_db()
    old = conn.execute(
        "SELECT foto_profile, foto_background FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    # ======================================================
    #  Upload Foto Profile
    # ======================================================
    foto_profile = request.files.get("foto_profile")
    foto_profile_name = old["foto_profile"]

    if foto_profile and foto_profile.filename != "":
        if not allowed_image(foto_profile.filename):
            conn.close()
            return "❌ Ekstensi foto profile tidak diizinkan!", 400

        # Hapus foto lama
        if foto_profile_name:
            old_path = os.path.join(PROFILE_FOLDER, foto_profile_name)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass

        foto_profile_name = f"profile_{user_id}_{secure_filename(foto_profile.filename)}"
        foto_profile.save(os.path.join(PROFILE_FOLDER, foto_profile_name))


    # ======================================================
    #  Upload Foto Background
    # ======================================================
    foto_background = request.files.get("foto_background")
    foto_background_name = old["foto_background"]

    if foto_background and foto_background.filename != "":
        if not allowed_image(foto_background.filename):
            conn.close()
            return "❌ Ekstensi foto background tidak diizinkan!", 400

        # Hapus foto lama
        if foto_background_name:
            old_path = os.path.join(PROFILE_BACKGROUND_FOLDER, foto_background_name)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass

        foto_background_name = f"background_{user_id}_{secure_filename(foto_background.filename)}"
        foto_background.save(os.path.join(PROFILE_BACKGROUND_FOLDER, foto_background_name))


    # ======================================================
    #  Update Database
    # ======================================================
    conn.execute("""
        UPDATE users SET 
            nama=?, umur=?, gender=?, email=?, bio=?,
            foto_profile=?, foto_background=?
        WHERE id=?
    """, (
        nama, umur, gender, email, bio,
        foto_profile_name, foto_background_name,
        user_id
    ))

    conn.commit()
    conn.close()

    # Update session biar live update
    session["foto_profile"] = foto_profile_name
    session["foto_background"] = foto_background_name

    # Redirect sesuai role
    role = session.get("role")
    if role in ("admin", "root"):
        return redirect("/admin/home")

    return redirect("/user/home")