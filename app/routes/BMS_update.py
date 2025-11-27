import os
from flask import Blueprint, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename

# 🔗 Ambil path resmi dari config
from app.BMS_config import UPLOAD_FOLDER
from app.routes.BMS_auth import BMS_auth_is_login, BMS_auth_is_admin, BMS_auth_is_root
from app.routes.BMS_logger import BMS_write_log

upload = Blueprint("upload", __name__, url_prefix="/upload")

# Pastikan folder upload ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ======================================================
#   🔐 Akses hanya admin / root
# ======================================================
def BMS_upload_required():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login!"}), 403

    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses ditolak!"}), 403

    return None


# ======================================================
#   🛡 Sanitasi filename
# ======================================================
def sanitize_filename(name):
    if not name:
        return None

    bad = ["..", "/", "\\", "|", "$", "`", ";"]
    for b in bad:
        if b in name:
            return None

    return secure_filename(name)


# ======================================================
#   ⬆ Upload file
# ======================================================
@upload.route("/", methods=["POST"])
def BMS_upload_file():
    check = BMS_upload_required()
    if check:
        return check

    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file!"})

    f = request.files["file"]
    filename = sanitize_filename(f.filename)

    if not filename:
        return jsonify({"error": "Nama file tidak valid!"})

    path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(path)

    BMS_write_log(f"Upload file: {path}", session.get("username"))

    return jsonify({"status": "ok", "path": path})


# ======================================================
#   📄 Download file
# ======================================================
@upload.route("/download")
def BMS_upload_download():
    check = BMS_upload_required()
    if check:
        return check

    filename = sanitize_filename(request.args.get("file"))
    if not filename:
        return "❌ File tidak valid!"

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)