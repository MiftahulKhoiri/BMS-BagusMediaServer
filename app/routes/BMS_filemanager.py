import os
import shutil
from werkzeug.utils import secure_filename
import zipfile
from flask import send_file
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

# --- Tambahkan import di bagian atas file (jika belum ada) ---


# --------------------------------------------------------------
#  Endpoint tambahan: raw (preview), upload, move, zip, unzip
# --------------------------------------------------------------

# ======================================================
#   ▶ Serve file tanpa attachment (preview inline)
# ======================================================
@filemanager.route("/raw")
def BMS_file_raw():
    check = BMS_fm_required()
    if check:
        return check

    path = safe_path(request.args.get("path"))
    username = session.get("username")

    if not path or not os.path.exists(path):
        BMS_write_log(f"Raw file tidak ditemukan: {path}", username)
        return jsonify({"error": "File tidak ditemukan!"}), 404

    # Catat preview
    BMS_write_log(f"Preview file: {path}", username)

    # Gunakan send_file agar dapat inline preview (content-disposition inline)
    try:
        return send_file(path)
    except Exception as e:
        BMS_write_log(f"Error raw send: {e}", username)
        return jsonify({"error": str(e)}), 500


# ======================================================
#   ⬆ Upload (drag & drop)
# ======================================================
@filemanager.route("/upload", methods=["POST"])
def BMS_file_upload():
    check = BMS_fm_required()
    if check:
        return check

    # target folder path (optional)
    target = safe_path(request.form.get("target")) or ROOT_PATH
    username = session.get("username")

    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file!"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({"error": "Nama file tidak valid!"}), 400

    dest = os.path.join(target, filename)
    # Safety: pastikan dest remains within ROOT_PATH
    dest = safe_path(dest)
    try:
        f.save(dest)
        BMS_write_log(f"Upload file: {dest}", username)
        return jsonify({"status": "ok", "path": dest})
    except Exception as e:
        BMS_write_log(f"Error upload: {e}", username)
        return jsonify({"error": str(e)}), 500


# ======================================================
#   ➡ Move (cut-paste) file/folder: POST old, new
# ======================================================
@filemanager.route("/move", methods=["POST"])
def BMS_file_move():
    check = BMS_fm_required()
    if check:
        return check

    old = safe_path(request.form.get("old"))
    new = safe_path(request.form.get("new"))
    username = session.get("username")

    if not old or not new:
        return jsonify({"error": "old/new tidak boleh kosong!"}), 400

    if not os.path.exists(old):
        return jsonify({"error": "Path lama tidak ditemukan!"}), 404

    try:
        os.makedirs(os.path.dirname(new), exist_ok=True)
        os.rename(old, new)
        BMS_write_log(f"Pindah: {old} -> {new}", username)
        return jsonify({"status": "moved", "old": old, "new": new})
    except Exception as e:
        BMS_write_log(f"Error move {old}: {e}", username)
        return jsonify({"error": str(e)}), 500


# ======================================================
#   📦 Zip folder/file: POST path, optional name (without ext)
# ======================================================
@filemanager.route("/zip", methods=["POST"])
def BMS_file_zip():
    check = BMS_fm_required()
    if check:
        return check

    path = safe_path(request.form.get("path"))
    name = request.form.get("name") or None
    username = session.get("username")

    if not path or not os.path.exists(path):
        return jsonify({"error": "Path tidak ditemukan!"}), 404

    # default name
    base = name or os.path.basename(path.rstrip("/")) or "archive"
    dest_zip = os.path.join(os.path.dirname(path), secure_filename(base) + ".zip")
    dest_zip = safe_path(dest_zip)

    try:
        # jika path file -> zip single file
        if os.path.isfile(path):
            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(path, arcname=os.path.basename(path))
        else:
            # folder -> zip recursively
            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(path):
                    for f in files:
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, os.path.dirname(path))
                        zf.write(full, arcname=arc)
        BMS_write_log(f"Zip dibuat: {dest_zip}", username)
        return jsonify({"status": "ok", "zip": dest_zip})
    except Exception as e:
        BMS_write_log(f"Error zip {path}: {e}", username)
        return jsonify({"error": str(e)}), 500


# ======================================================
#   📤 Unzip: POST path (zip file), optional dest
# ======================================================
@filemanager.route("/unzip", methods=["POST"])
def BMS_file_unzip():
    check = BMS_fm_required()
    if check:
        return check

    zip_path = safe_path(request.form.get("path"))
    dest = safe_path(request.form.get("dest") or os.path.dirname(zip_path))
    username = session.get("username")

    if not zip_path or not os.path.exists(zip_path):
        return jsonify({"error": "ZIP tidak ditemukan!"}), 404

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest)
        BMS_write_log(f"Unzip: {zip_path} -> {dest}", username)
        return jsonify({"status": "ok", "dest": dest})
    except Exception as e:
        BMS_write_log(f"Error unzip {zip_path}: {e}", username)
        return jsonify({"error": str(e)}), 500


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