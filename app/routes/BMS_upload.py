import os
from flask import Blueprint, render_template, request, redirect, jsonify
from app.routes.BMS_auth import (
    BMS_auth_is_login,
)

upload = Blueprint("upload", __name__, url_prefix="/upload")

# Folder tempat file diupload
UPLOAD_FOLDER = "/storage/emulated/0/BMS/UPLOAD"

# Pastikan folder ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ======================================================
#   🔐 Proteksi Akses Upload
# ======================================================
def BMS_upload_required():
    """Hanya user login yang boleh upload file."""
    if not BMS_auth_is_login():
        return redirect("/auth/login")
    return None


# ======================================================
#   📤 Halaman Upload File
# ======================================================
@upload.route("/")
def BMS_upload_page():
    """
    Menampilkan halaman BMS_upload.html
    """
    check = BMS_upload_required()
    if check:
        return check

    return render_template("BMS_upload.html")


# ======================================================
#   📤 API Upload File
# ======================================================
@upload.route("/do", methods=["POST"])
def BMS_upload_do():
    """
    Menerima file dari user,
    menyimpannya di UPLOAD_FOLDER,
    dan mengembalikan notif.
    """
    check = BMS_upload_required()
    if check:
        return check

    if "file" not in request.files:
        return "❌ Tidak ada file."

    file = request.files["file"]

    if file.filename == "":
        return "❌ Nama file kosong."

    # Simpan file
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    return f"✔ File '{file.filename}' berhasil diupload!"