import os
import shutil
from flask import Blueprint, request, jsonify, send_from_directory
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

filemanager = Blueprint("filemanager", __name__, url_prefix="/filemanager")

# Folder dasar untuk file manager
ROOT_PATH = "/storage/emulated/0/BMS/"


# ======================================================
#   🔐 Proteksi Admin
# ======================================================
def BMS_fm_required():
    if not BMS_auth_is_login():
        return jsonify({"error": "Anda belum login!"}), 403

    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return jsonify({"error": "Akses ditolak!"}), 403

    return None


# ======================================================
#   📁 API: List Folder dan File
# ======================================================
@filemanager.route("/list")
def BMS_file_list():
    check = BMS_fm_required()
    if check:
        return check

    path = request.args.get("path", ROOT_PATH)

    if not os.path.exists(path):
        return jsonify({"error": "Path tidak ditemukan!"})

    items = []

    for name in os.listdir(path):
        fullpath = os.path.join(path, name)
        items.append({
            "name": name,
            "path": fullpath,
            "is_dir": os.path.isdir(fullpath)
        })

    return jsonify({
        "current": path,
        "items": items
    })


# ======================================================
#   📤 Download File
# ======================================================
@filemanager.route("/download")
def BMS_file_download():
    check = BMS_fm_required()
    if check:
        return check

    path = request.args.get("path")
    if not path:
        return "❌ Path kosong!"

    folder = os.path.dirname(path)
    filename = os.path.basename(path)

    return send_from_directory(folder, filename, as_attachment=True)


# ======================================================
#   🗑 Hapus File / Folder
# ======================================================
@filemanager.route("/delete", methods=["POST"])
def BMS_file_delete():
    check = BMS_fm_required()
    if check:
        return check

    path = request.form.get("path")

    if os.path.isdir(path):
        shutil.rmtree(path)
        return "✔ Folder dihapus!"
    else:
        os.remove(path)
        return "✔ File dihapus!"


# ======================================================
#   ✏ Rename File / Folder
# ======================================================
@filemanager.route("/rename", methods=["POST"])
def BMS_file_rename():
    check = BMS_fm_required()
    if check:
        return check

    old = request.form.get("old")
    new = request.form.get("new")

    os.rename(old, new)

    return "✔ Berhasil rename!"


# ======================================================
#   📂 Buat Folder Baru
# ======================================================
@filemanager.route("/mkdir", methods=["POST"])
def BMS_file_mkdir():
    check = BMS_fm_required()
    if check:
        return check

    newpath = request.form.get("path")
    os.makedirs(newpath, exist_ok=True)

    return "✔ Folder berhasil dibuat!"