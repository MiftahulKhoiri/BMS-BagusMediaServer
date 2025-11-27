import os
import shutil
import zipfile
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session, send_file, send_from_directory

# 🔗 Import folder root dari Config BMS
from app.BMS_config import BASE
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

filemanager = Blueprint("filemanager", __name__, url_prefix="/filemanager")

# =========================================
# 🔥 ROOT FILEMANAGER = BASE (Config)
# =========================================
ROOT_PATH = BASE
os.makedirs(ROOT_PATH, exist_ok=True)


# --------------------------------------------------------------
#   📌 Helper: Path Sanitizer (anti hack)
# --------------------------------------------------------------
def safe_path(path):
    """
    Membersihkan path agar TIDAK bisa keluar dari BASE folder.
    """
    if not path:
        return ROOT_PATH

    real = os.path.abspath(path)

    # Pastikan TIDAK bisa keluar dari BASE
    if not real.startswith(ROOT_PATH):
        return ROOT_PATH

    return real


# --------------------------------------------------------------
# 🔐 Hak akses FileManager
# --------------------------------------------------------------
def BMS_fm_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses FileManager ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Anda belum login!"}), 403

    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        BMS_write_log("Akses FileManager ditolak (tanpa izin)", session.get("username"))
        return jsonify({"error": "Akses ditolak!"}), 403

    return None


# ======================================================
#   ▶ RAW FILE PREVIEW
# ======================================================
@filemanager.route("/raw")
def BMS_file_raw():
    check = BMS_fm_required()
    if check: return check

    path = safe_path(request.args.get("path"))
    username = session.get("username")

    if not os.path.exists(path):
        return jsonify({"error": "File tidak ditemukan!"}), 404

    BMS_write_log(f"Preview file: {path}", username)

    try:
        return send_file(path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#   ⬆ UPLOAD FILE
# ======================================================
@filemanager.route("/upload", methods=["POST"])
def BMS_file_upload():
    check = BMS_fm_required()
    if check: return check

    target = safe_path(request.form.get("target")) or ROOT_PATH
    username = session.get("username")

    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file!"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)

    dest = safe_path(os.path.join(target, filename))

    try:
        f.save(dest)
        BMS_write_log(f"Upload file: {dest}", username)
        return jsonify({"status": "ok", "path": dest})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#   ➡ MOVE FILE
# ======================================================
@filemanager.route("/move", methods=["POST"])
def BMS_file_move():
    check = BMS_fm_required()
    if check: return check

    old = safe_path(request.form.get("old"))
    new = safe_path(request.form.get("new"))
    username = session.get("username")

    if not os.path.exists(old):
        return jsonify({"error": "Path lama tidak ditemukan"}), 404

    try:
        os.makedirs(os.path.dirname(new), exist_ok=True)
        os.rename(old, new)
        BMS_write_log(f"Pindah: {old} -> {new}", username)
        return jsonify({"status": "moved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#   📦 ZIP FILE / FOLDER
# ======================================================
@filemanager.route("/zip", methods=["POST"])
def BMS_file_zip():
    check = BMS_fm_required()
    if check: return check

    path = safe_path(request.form.get("path"))
    name = request.form.get("name") or os.path.basename(path)

    username = session.get("username")

    dest_zip = safe_path(os.path.join(os.path.dirname(path), secure_filename(name) + ".zip"))

    try:
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isfile(path):
                zf.write(path, arcname=os.path.basename(path))
            else:
                for root, dirs, files in os.walk(path):
                    for f in files:
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, os.path.dirname(path))
                        zf.write(full, arcname=arc)

        BMS_write_log(f"Zip dibuat: {dest_zip}", username)
        return jsonify({"status": "ok", "zip": dest_zip})
    except Exception as e:
        return jsonify({"error": str(e)})


# ======================================================
#   📤 UNZIP
# ======================================================
@filemanager.route("/unzip", methods=["POST"])
def BMS_file_unzip():
    check = BMS_fm_required()
    if check: return check

    zip_path = safe_path(request.form.get("path"))
    dest = safe_path(request.form.get("dest") or os.path.dirname(zip_path))
    username = session.get("username")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest)

        BMS_write_log(f"Unzip: {zip_path} -> {dest}", username)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ======================================================
#   📄 LIST FILE
# ======================================================
@filemanager.route("/list")
def BMS_file_list():
    check = BMS_fm_required()
    if check: return check

    path = safe_path(request.args.get("path") or ROOT_PATH)
    username = session.get("username")

    if not os.path.exists(path):
        return jsonify({"error": "Path tidak ditemukan!"})

    items = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        items.append({
            "name": name,
            "path": full,
            "is_dir": os.path.isdir(full)
        })

    BMS_write_log(f"List folder: {path}", username)
    return jsonify({"current": path, "items": items})


# ======================================================
#   📥 DOWNLOAD FILE
# ======================================================
@filemanager.route("/download")
def BMS_file_download():
    check = BMS_fm_required()
    if check: return check

    path = safe_path(request.args.get("path"))
    username = session.get("username")

    folder = os.path.dirname(path)
    filename = os.path.basename(path)

    return send_from_directory(folder, filename, as_attachment=True)


# ======================================================
#   🗑 DELETE
# ======================================================
@filemanager.route("/delete", methods=["POST"])
def BMS_file_delete():
    check = BMS_fm_required()
    if check: return check

    path = safe_path(request.form.get("path"))
    username = session.get("username")

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

        BMS_write_log(f"Hapus: {path}", username)
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ======================================================
#   ✏ RENAME
# ======================================================
@filemanager.route("/rename", methods=["POST"])
def BMS_file_rename():
    check = BMS_fm_required()
    if check: return check

    old = safe_path(request.form.get("old"))
    new = safe_path(request.form.get("new"))
    username = session.get("username")

    try:
        os.rename(old, new)
        BMS_write_log(f"Rename: {old} -> {new}", username)
        return jsonify({"status": "renamed"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ======================================================
#   📂 MKDIR
# ======================================================
@filemanager.route("/mkdir", methods=["POST"])
def BMS_file_mkdir():
    check = BMS_fm_required()
    if check: return check

    path = safe_path(request.form.get("path"))
    username = session.get("username")

    try:
        os.makedirs(path, exist_ok=True)
        BMS_write_log(f"Buat folder: {path}", username)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)})