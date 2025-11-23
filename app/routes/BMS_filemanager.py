from flask import Blueprint, request, jsonify, send_from_directory
import os
import shutil
from werkzeug.utils import secure_filename

filem = Blueprint("filem", __name__, url_prefix="/files")

# ======================================
#  Konfigurasi dasar
# ======================================

BASE_PATH = os.path.abspath("storage")   # semua file disimpan di folder storage/


# Pastikan folder storage ada
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)


# ======================================
#  DAFTAR FILE & FOLDER
# ======================================

@filem.route("/list")
def BMS_file_list():
    path = request.args.get("path", "")
    target = os.path.join(BASE_PATH, path)

    if not os.path.exists(target):
        return jsonify({"error": "Path tidak ditemukan"}), 400

    items = os.listdir(target)

    folders = [x for x in items if os.path.isdir(os.path.join(target, x))]
    files   = [x for x in items if os.path.isfile(os.path.join(target, x))]

    return jsonify({
        "path": path,
        "folders": folders,
        "files": files
    })


# ======================================
#  RENAME FILE / FOLDER
# ======================================

@filem.route("/rename", methods=["POST"])
def BMS_file_rename():
    old = request.form.get("old")
    new = request.form.get("new")

    old_path = os.path.join(BASE_PATH, old)
    new_path = os.path.join(BASE_PATH, new)

    if not os.path.exists(old_path):
        return "File tidak ditemukan!"

    os.rename(old_path, new_path)
    return "Rename berhasil!"


# ======================================
#  DELETE FILE
# ======================================

@filem.route("/delete", methods=["POST"])
def BMS_file_delete():
    path = request.form.get("path")
    target = os.path.join(BASE_PATH, path)

    if not os.path.exists(target):
        return "File tidak ditemukan!"

    if os.path.isfile(target):
        os.remove(target)
        return "File dihapus!"

    return "Bukan file!"


# ======================================
#  DELETE FOLDER
# ======================================

@filem.route("/delete-folder", methods=["POST"])
def BMS_file_delete_folder():
    path = request.form.get("path")
    target = os.path.join(BASE_PATH, path)

    if not os.path.exists(target):
        return "Folder tidak ditemukan!"

    if os.path.isdir(target):
        shutil.rmtree(target)
        return "Folder dihapus!"

    return "Bukan folder!"


# ======================================
#  UPLOAD FILE
# ======================================

@filem.route("/upload", methods=["POST"])
def BMS_file_upload():
    if "file" not in request.files:
        return "Tidak ada file!"

    file = request.files["file"]
    folder = request.form.get("folder", "")

    save_path = os.path.join(BASE_PATH, folder)

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    filename = secure_filename(file.filename)
    file.save(os.path.join(save_path, filename))

    return "Upload berhasil!"


# ======================================
#  BUAT FOLDER BARU
# ======================================

@filem.route("/newfolder", methods=["POST"])
def BMS_file_newfolder():
    folder = request.form.get("folder")
    target = os.path.join(BASE_PATH, folder)

    if os.path.exists(target):
        return "Folder sudah ada!"

    os.makedirs(target)
    return "Folder berhasil dibuat!"


# ======================================
#  DOWNLOAD FILE
# ======================================

@filem.route("/download")
def BMS_file_download():
    path = request.args.get("path")
    folder = os.path.dirname(path)
    file = os.path.basename(path)

    full_path = os.path.join(BASE_PATH, folder)

    if not os.path.exists(os.path.join(full_path, file)):
        return "File tidak ditemukan!"

    return send_from_directory(full_path, file, as_attachment=True)