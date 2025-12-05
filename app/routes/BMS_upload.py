import os
import zipfile
import shutil
import hashlib
import tarfile
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
    send_from_directory,
    Response,
    render_template
)
from werkzeug.utils import secure_filename

# ROOT dan Auth
from app.BMS_config import BASE
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log


# ===============================================================
# FIX: BLUEPRINT NAME
# ===============================================================
upload = Blueprint("upload", __name__, url_prefix="/upload")

# ROOT folder BMS
ROOT = BASE


# ===============================================================
# SAFETY FUNCTION
# ===============================================================
def safe(p):
    """Memastikan path tetap aman dalam ROOT directory."""
    if not p:
        return ROOT
    real = os.path.abspath(p)
    if not real.startswith(ROOT):
        return ROOT
    return real


# Auth middleware
def fm_auth():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses ditolak"}), 403
    return None


# ===============================================================
# INTERNAL STORAGE
# ===============================================================
UPLOAD_INTERNAL = ".uploads"
BACKUP_INTERNAL = ".backups"

upload_sessions = {}
upload_lock = Lock()


def safe_internal(*paths):
    base = os.path.join(ROOT, *paths)
    real = os.path.abspath(base)
    if not real.startswith(ROOT):
        real = ROOT
    return real


# ===============================================================
# START UPLOAD
# ===============================================================
@upload.route("/upload_chunk/start", methods=["POST"])
def fm_chunk_start():
    check = fm_auth()
    if check:
        return check

    filename = secure_filename(request.form.get("name"))
    file_size = int(request.form.get("total_size", 0))
    file_md5 = request.form.get("file_md5", "")

    # Batas 1GB
    MAX_SIZE = 1 * 1024 * 1024 * 1024
    if file_size > MAX_SIZE:
        return jsonify({"error": "Max file size 1GB"}), 400

    session_id = str(uuid.uuid4())
    temp_filename = f"{session_id}_{filename}.part"
    temp_path = safe_internal(UPLOAD_INTERNAL, temp_filename)

    os.makedirs(safe_internal(UPLOAD_INTERNAL), exist_ok=True)

    with upload_lock:
        upload_sessions[session_id] = {
            "filename": filename,
            "temp_path": temp_path,
            "file_size": file_size,
            "uploaded_size": 0,
            "chunk_count": 0,
            "file_md5": file_md5,
            "start_time": time.time(),
            "last_update": time.time(),
            "user_id": session.get("user_id", "unknown")
        }

    open(temp_path, "wb").close()

    return jsonify({
        "session_id": session_id,
        "temp": temp_filename,
        "recommended_chunk_size": 1024 * 1024
    })


# ===============================================================
# APPEND CHUNK
# ===============================================================
@upload.route("/upload_chunk/append", methods=["POST"])
def fm_chunk_append():
    check = fm_auth()
    if check:
        return check

    session_id = request.form.get("session_id")
    chunk_index = int(request.form.get("chunk_index", 0))

    if session_id not in upload_sessions:
        return jsonify({"error": "Session invalid"}), 400

    session_data = upload_sessions[session_id]
    temp_path = session_data["temp_path"]

    chunk = request.files.get("chunk")
    if not chunk:
        return jsonify({"error": "Chunk missing"}), 400

    chunk_data = chunk.read()

    expected_index = session_data["chunk_count"]
    if chunk_index != expected_index:
        return jsonify({
            "error": "Chunk index mismatch",
            "expected": expected_index,
            "got": chunk_index
        }), 409

    new_total_size = session_data["uploaded_size"] + len(chunk_data)
    if new_total_size > session_data["file_size"]:
        return jsonify({"error": "File size exceeded"}), 400

    try:
        with open(temp_path, "ab", buffering=1048576) as f:
            f.write(chunk_data)
    except Exception as e:
        return jsonify({"error": f"Write error: {str(e)}"}), 500

    with upload_lock:
        session_data["uploaded_size"] = new_total_size
        session_data["chunk_count"] += 1
        session_data["last_update"] = time.time()

    progress = (new_total_size / session_data["file_size"]) * 100

    return jsonify({
        "status": "ok",
        "progress": round(progress, 2),
        "uploaded_size": new_total_size,
        "chunk_index": chunk_index
    })


# ===============================================================
# FINISH UPLOAD (AUTO SORT)
# ===============================================================
@upload.route("/upload_chunk/finish", methods=["POST"])
def fm_chunk_finish():
    check = fm_auth()
    if check:
        return check

    session_id = request.form.get("session_id")
    final_filename = secure_filename(request.form.get("final_filename"))

    if session_id not in upload_sessions:
        return jsonify({"error": "Session invalid"}), 400

    session_data = upload_sessions[session_id]
    temp_path = session_data["temp_path"]

    try:
        # Verifikasi ukuran
        actual_size = os.path.getsize(temp_path)
        if actual_size != session_data["file_size"]:
            return jsonify({"error": "File size mismatch"}), 400

        # Verifikasi MD5
        if session_data["file_md5"]:
            file_hash = hashlib.md5()
            with open(temp_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    file_hash.update(chunk)
            if file_hash.hexdigest() != session_data["file_md5"]:
                return jsonify({"error": "MD5 mismatch"}), 400

        # ----------------------------------------------------------
        # AUTO SORT
        # ----------------------------------------------------------
        ext = os.path.splitext(final_filename)[1].lower()

        CATEGORY_MAP = {
            "music": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "video": [".mp4", ".mkv", ".mov", ".avi", ".flv"],
            "photo": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "docs": [".pdf", ".txt", ".docx", ".xlsx", ".csv"],
            "archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "apps": [".apk", ".exe", ".iso"],
        }

        target_folder = "others"
        for folder, exts in CATEGORY_MAP.items():
            if ext in exts:
                target_folder = folder
                break

        final_dir = safe(os.path.join(ROOT, target_folder))
        os.makedirs(final_dir, exist_ok=True)

        final_path = safe(os.path.join(final_dir, final_filename))

        # ----------------------------------------------------------
        # BACKUP jika file sudah ada
        # ----------------------------------------------------------
        os.makedirs(safe_internal(BACKUP_INTERNAL), exist_ok=True)

        if os.path.exists(final_path):
            backup_path = safe_internal(
                BACKUP_INTERNAL,
                f"{final_filename}.backup.{int(time.time())}"
            )
            shutil.move(final_path, backup_path)

        # Move file final
        os.rename(temp_path, final_path)

        # Statistik upload
        upload_time = time.time() - session_data["start_time"]
        speed = session_data["file_size"] / upload_time

        with upload_lock:
            del upload_sessions[session_id]

        return jsonify({
            "status": "finished",
            "sorted_folder": target_folder,
            "final_path": final_path,
            "file_size": actual_size,
            "upload_time": round(upload_time, 2),
            "speed_bytes": round(speed, 2),
            "chunks_processed": session_data["chunk_count"]
        })

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


# ===============================================================
# CANCEL UPLOAD
# ===============================================================
@upload.route("/upload_chunk/cancel", methods=["POST"])
def fm_chunk_cancel():
    check = fm_auth()
    if check:
        return check

    session_id = request.form.get("session_id")

    if session_id in upload_sessions:
        temp = upload_sessions[session_id]["temp_path"]

        if os.path.exists(temp):
            try:
                os.remove(temp)
            except:
                pass

        with upload_lock:
            del upload_sessions[session_id]

    return jsonify({"status": "cancelled"})


# ===============================================================
# STATUS UPLOAD
# ===============================================================
@upload.route("/upload_chunk/status")
def fm_chunk_status():
    check = fm_auth()
    if check:
        return check

    session_id = request.args.get("session_id")

    if session_id not in upload_sessions:
        return jsonify({"error": "Session not found"}), 404

    d = upload_sessions[session_id]

    return jsonify({
        "filename": d["filename"],
        "uploaded_size": d["uploaded_size"],
        "total_size": d["file_size"],
        "progress": round((d["uploaded_size"] / d["file_size"]) * 100, 2),
        "chunk_count": d["chunk_count"],
        "user_id": d["user_id"],
        "last_update": d["last_update"]
    })


# ===============================================================
# UI ROUTE
# ===============================================================
@upload.route("/ui")
def fm_upload_ui():
    check = fm_auth()
    if check:
        return check

    return render_template("BMS_upload.html")