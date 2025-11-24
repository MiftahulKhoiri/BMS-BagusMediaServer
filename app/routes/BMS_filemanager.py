import os
import shutil
from flask import Blueprint, request, jsonify, session, send_from_directory
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

filemanager = Blueprint("filemanager", __name__, url_prefix="/filemanager")

ROOT_PATH = "/storage/emulated/0/BMS/"
os.makedirs(ROOT_PATH, exist_ok=True)


# ======================================================
#   🛡 PATH SANITIZER (anti hack)
# ======================================================
def safe_path(path):
    if not path:
        return ROOT_PATH

    path = os.path.abspath(path)

    if not path.startswith(ROOT_PATH):
        return ROOT_PATH

    return path


# ======================================================
#   🔐 Proteksi Admin
# ======================================================
def BMS_fm_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses FileManager ditolak (belum login)", "UNKNOWN")
        return jsonify({"error": "Anda belum login!"}), 403

    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        BMS_write_log("Akses FileManager ditolak (tanpa izin)", session.get("username"))
        return jsonify({"error": "Akses ditolak!"}), 403

    return None


# ======================================================
#   📄 List File & Folder
# ======================================================
@filemanager.route("/list")
def BMS_file_list():
    check = BMS_fm_required()
    if check:
        return check

    path = safe_path(request.args.get("path", ROOT_PATH))
    username = session.get("username")

    if not os.path.exists(path):
        return jsonify({"error": "Path tidak ditemukan!"})

    BMS_write_log(f"List folder: {path}", username)

    try:
        items = [
            {
                "name": name,
                "path": os.path.join(path, name),
                "is_dir": os.path.isdir(os.path.join(path, name))
            }
            for name in os.listdir(path)
        ]

        return jsonify({
            "current": path,
            "items": items
        })

    except Exception as e:
        BMS_write_log(f"Error list folder: {path} -> {e}", username)
        return jsonify({"error": str(e)})


# ======================================================
#   📥 Download File
# ======================================================
@filemanager.route("/download")
def BMS_file_download():
    check = BMS_fm_required()
    if check:
        return check

    path = safe_path(request.args.get("path"))
    username = session.get("username")

    if not os.path.exists(path):
        return "❌ File tidak ditemukan!"

    BMS_write_log(f"Download file: {path}", username)

    folder = os.path.dirname(path)
    filename = os.path.basename(path)

    return send_from_directory(folder, filename, as_attachment=True)


# ======================================================
#   🗑 Delete File / Folder
# ======================================================
@filemanager.route("/delete", methods=["POST"])
def BMS_file_delete():
    check = BMS_fm_required()
    if check:
        return check

    path = safe_path(request.form.get("path"))
    username = session.get("username")

    if not os.path.exists(path):
        return jsonify({"error": "Path tidak ditemukan!"})

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            BMS_write_log(f"Hapus folder: {path}", username)
            return jsonify({"status": "Folder dihapus"})
        else:
            os.remove(path)
            BMS_write_log(f"Hapus file: {path}", username)
            return jsonify({"status": "File dihapus"})

    except Exception as e:
        BMS_write_log(f"Error delete {path}: {e}", username)
        return jsonify({"error": str(e)})


# ======================================================
#   ✏ Rename File / Folder
# ======================================================
@filemanager.route("/rename", methods=["POST"])
def BMS_file_rename():
    check = BMS_fm_required()
    if check:
        return check

    old = safe_path(request.form.get("old"))
    new = safe_path(request.form.get("new"))
    username = session.get("username")

    if not old or not new:
        return jsonify({"error": "Nama kosong!"})

    try:
        os.rename(old, new)
        BMS_write_log(f"Rename: {old} → {new}", username)
        return jsonify({"status": "Rename berhasil"})
    except Exception as e:
        BMS_write_log(f"Error rename {old}: {e}", username)
        return jsonify({"error": str(e)})


# ======================================================
#   📂 Create Folder
# ======================================================
@filemanager.route("/mkdir", methods=["POST"])
def BMS_file_mkdir():
    check = BMS_fm_required()
    if check:
        return check

    path = safe_path(request.form.get("path"))
    username = session.get("username")

    if not path:
        return jsonify({"error": "Nama folder kosong!"})

    try:
        os.makedirs(path, exist_ok=True)
        BMS_write_log(f"Buat folder: {path}", username)
        return jsonify({"status": "Folder dibuat"})
    except Exception as e:
        BMS_write_log(f"Error mkdir {path}: {e}", username)
        return jsonify({"error": str(e)})