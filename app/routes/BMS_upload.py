import os
import zipfile
import shutil
import hashlib
import time
import base64
import uuid
from threading import Lock
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    send_file,
    Response,
    render_template
)
from werkzeug.utils import secure_filename

from app.BMS_config import BASE
from app.routes.BMS_auth.session_helpers import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log


upload = Blueprint("upload", __name__, url_prefix="/upload")

ROOT = os.path.realpath(BASE)
UPLOAD_INTERNAL = ".uploads"
BACKUP_INTERNAL = ".backups"

upload_lock = Lock()
upload_sessions = {}   # { session_id : {...} }


# ================================================================
# SAFE PATH VALIDATION
# ================================================================
def safe_path(path):
    """ Pastikan path selalu di bawah ROOT directory. """
    if not path:
        return ROOT
    real = os.path.realpath(path)
    if not real.startswith(ROOT):
        return ROOT
    return real


def internal_path(*paths):
    """ Path internal aman (tidak bisa ditraversal) """
    base = os.path.join(ROOT, *paths)
    real = os.path.realpath(base)
    if not real.startswith(ROOT):
        raise Exception("Blocked path traversal attempt")
    return real


# ================================================================
# AUTH MIDDLEWARE
# ================================================================
def fm_auth():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses ditolak"}), 403
    return None


# ================================================================
# DISK SPACE PROTECTION
# ================================================================
def check_disk_space(required):
    """ Pastikan tersedia ruang minimal 2× ukuran file. """
    stat = shutil.disk_usage(ROOT)
    free = stat.free
    return free > (required * 2)  # aman jika ada dua kali kapasitas


# ================================================================
# START CHUNK SESSION
# ================================================================
@upload.route("/upload_chunk/start", methods=["POST"])
def upload_start():
    cek = fm_auth()
    if cek:
        return cek

    filename = secure_filename(request.form.get("name", "file"))
    total_size = int(request.form.get("total_size", 0))
    md5 = request.form.get("file_md5", "")

    MAX_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB limit
    if total_size > MAX_SIZE:
        return jsonify({"error": "File terlalu besar (maks 2GB)"}), 400

    if not check_disk_space(total_size):
        return jsonify({"error": "Ruang penyimpanan tidak cukup"}), 507

    session_id = str(uuid.uuid4())
    temp_name = f"{session_id}_{filename}.part"
    temp_path = internal_path(UPLOAD_INTERNAL, temp_name)

    os.makedirs(internal_path(UPLOAD_INTERNAL), exist_ok=True)
    open(temp_path, "wb").close()

    with upload_lock:
        upload_sessions[session_id] = {
            "filename": filename,
            "temp_path": temp_path,
            "file_size": total_size,
            "uploaded_size": 0,
            "chunk_count": 0,
            "file_md5": md5,
            "start_time": time.time(),
            "user_id": session.get("user_id")
        }

    return jsonify({
        "session_id": session_id,
        "temp": temp_name,
        "recommended_chunk": 1024 * 1024
    })


# ================================================================
# APPEND CHUNK
# ================================================================
@upload.route("/upload_chunk/append", methods=["POST"])
def upload_append():
    cek = fm_auth()
    if cek:
        return cek

    session_id = request.form.get("session_id")
    index = int(request.form.get("chunk_index", 0))

    if session_id not in upload_sessions:
        return jsonify({"error": "Session tidak valid"}), 404

    data = upload_sessions[session_id]
    temp_path = data["temp_path"]

    chunk = request.files.get("chunk")
    if not chunk:
        return jsonify({"error": "Chunk kosong"}), 400

    chunk_bytes = chunk.read()

    # VALIDASI INDEX
    if index != data["chunk_count"]:
        return jsonify({
            "error": "Index mismatch",
            "expected": data["chunk_count"],
            "got": index,
        }), 409

    # VALIDASI UKURAN
    new_size = data["uploaded_size"] + len(chunk_bytes)
    if new_size > data["file_size"]:
        return jsonify({"error": "Ukuran file berlebih"}), 400

    # TULIS CHUNK
    try:
        with open(temp_path, "ab", buffering=1048576) as f:
            f.write(chunk_bytes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # UPDATE STATUS
    with upload_lock:
        data["uploaded_size"] = new_size
        data["chunk_count"] += 1

    progress = (new_size / data["file_size"]) * 100

    return jsonify({
        "status": "ok",
        "progress": round(progress, 2),
        "uploaded": new_size,
        "chunk_index": index
    })


# ================================================================
# FINISH UPLOAD
# ================================================================
CATEGORIES = {
    "music": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "video": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "docs":  [".pdf", ".txt", ".docx", ".xlsx", ".csv"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
}

@upload.route("/upload_chunk/finish", methods=["POST"])
def upload_finish():
    cek = fm_auth()
    if cek:
        return cek

    session_id = request.form.get("session_id")
    finalname = secure_filename(request.form.get("final_filename", ""))

    if session_id not in upload_sessions:
        return jsonify({"error": "Session invalid"}), 400

    data = upload_sessions[session_id]
    temp_path = data["temp_path"]

    # VALIDASI AKHIR
    if os.path.getsize(temp_path) != data["file_size"]:
        return jsonify({"error": "Size mismatch"}), 409

    # VALIDASI MD5 (jika diberikan)
    if data["file_md5"]:
        h = hashlib.md5()
        with open(temp_path, "rb") as f:
            for c in iter(lambda: f.read(8192), b""):
                h.update(c)
        if h.hexdigest() != data["file_md5"]:
            return jsonify({"error": "MD5 tidak cocok"}), 400

    # -------------------------------
    # SORT KATEGORI FILE
    # -------------------------------
    ext = os.path.splitext(finalname)[1].lower()
    target_dir = "others"

    for folder, exts in CATEGORIES.items():
        if ext in exts:
            target_dir = folder
            break

    final_folder = safe_path(os.path.join(ROOT, target_dir))
    os.makedirs(final_folder, exist_ok=True)

    final_path = safe_path(os.path.join(final_folder, finalname))

    # BACKUP jika file sudah ada
    bdir = internal_path(BACKUP_INTERNAL)
    os.makedirs(bdir, exist_ok=True)

    if os.path.exists(final_path):
        backup_name = f"{finalname}.bak.{int(time.time())}"
        shutil.move(final_path, os.path.join(bdir, backup_name))

    # Move final file
    shutil.move(temp_path, final_path)

    # Hitung waktu dan kecepatan
    duration = max(0.001, time.time() - data["start_time"])
    speed = data["file_size"] / duration

    del upload_sessions[session_id]

    return jsonify({
        "status": "finished",
        "folder": target_dir,
        "filepath": final_path,
        "size": data["file_size"],
        "duration_sec": round(duration, 2),
        "speed_bps": round(speed, 2)
    })


# ================================================================
# CANCEL
# ================================================================
@upload.route("/upload_chunk/cancel", methods=["POST"])
def upload_cancel():
    cek = fm_auth()
    if cek:
        return cek

    session_id = request.form.get("session_id")

    if session_id in upload_sessions:
        temp = upload_sessions[session_id]["temp_path"]
        if os.path.exists(temp):
            os.remove(temp)
        del upload_sessions[session_id]

    return jsonify({"status": "cancelled"})


# ================================================================
# STATUS
# ================================================================
@upload.route("/upload_chunk/status")
def upload_status():
    cek = fm_auth()
    if cek:
        return cek

    sid = request.args.get("session_id")
    if sid not in upload_sessions:
        return jsonify({"error": "Session tidak ditemukan"}), 404

    d = upload_sessions[sid]
    return jsonify({
        "filename": d["filename"],
        "uploaded": d["uploaded_size"],
        "total": d["file_size"],
        "progress": round((d["uploaded_size"] / d["file_size"]) * 100, 2),
        "chunks": d["chunk_count"],
        "user_id": d["user_id"],
        "started_at": d["start_time"],
    })


# ================================================================
# UPLOAD UI
# ================================================================
@upload.route("/ui")
def upload_ui():
    cek = fm_auth()
    if cek:
        return cek
    return render_template("BMS_upload.html")