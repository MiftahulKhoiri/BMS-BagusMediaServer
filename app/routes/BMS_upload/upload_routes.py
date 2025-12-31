import os
import uuid
import time
import shutil
import threading
import hashlib

from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename

from .upload_auth import fm_auth
from .upload_paths import (
    ROOT, UPLOAD_INTERNAL, BACKUP_INTERNAL,
    safe_path, internal_path
)
from .upload_sessions import upload_lock, upload_sessions
from .upload_utils import check_disk_space

upload = Blueprint("upload", __name__, url_prefix="/upload")

# =========================================================
# HELPER
# =========================================================
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =========================================================
# START UPLOAD SESSION
# POST /upload/upload_chunk/start
# =========================================================
@upload.route("/upload_chunk/start", methods=["POST"])
@fm_auth
def upload_start():
    filename = secure_filename(request.form.get("name", ""))
    total_size = int(request.form.get("total_size", 0))

    if not filename or total_size <= 0:
        return jsonify({"error": "Invalid file"}), 400

    if not check_disk_space(total_size):
        return jsonify({"error": "Disk penuh"}), 507

    session_id = uuid.uuid4().hex
    tmp_dir = os.path.join(UPLOAD_INTERNAL, session_id)
    os.makedirs(tmp_dir, exist_ok=True)

    with upload_lock:
        upload_sessions[session_id] = {
            "filename": filename,
            "total_size": total_size,
            "received": 0,
            "tmp_dir": tmp_dir,
            "created": time.time()
        }

    return jsonify({
        "session_id": session_id
    })


# =========================================================
# APPEND CHUNK
# POST /upload/upload_chunk/append
# =========================================================
@upload.route("/upload_chunk/append", methods=["POST"])
@fm_auth
def upload_append():
    session_id = request.form.get("session_id")
    chunk_index = request.form.get("chunk_index")
    chunk = request.files.get("chunk")

    if not session_id or chunk is None:
        return jsonify({"error": "Invalid chunk"}), 400

    with upload_lock:
        info = upload_sessions.get(session_id)

    if not info:
        return jsonify({"error": "Session not found"}), 404

    chunk_name = f"{int(chunk_index):06d}.part"
    chunk_path = os.path.join(info["tmp_dir"], chunk_name)

    chunk.save(chunk_path)

    size = os.path.getsize(chunk_path)

    with upload_lock:
        info["received"] += size
        progress = int((info["received"] / info["total_size"]) * 100)

    return jsonify({
        "progress": min(progress, 100)
    })


# =========================================================
# FINISH UPLOAD
# POST /upload/upload_chunk/finish
# =========================================================
@upload.route("/upload_chunk/finish", methods=["POST"])
@fm_auth
def upload_finish():
    session_id = request.form.get("session_id")
    final_filename = secure_filename(request.form.get("final_filename", ""))

    if not session_id or not final_filename:
        return jsonify({"error": "Invalid finish"}), 400

    with upload_lock:
        info = upload_sessions.pop(session_id, None)

    if not info:
        return jsonify({"error": "Session not found"}), 404

    final_path = internal_path(final_filename)
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    # gabungkan semua chunk
    with open(final_path, "wb") as out:
        for part in sorted(os.listdir(info["tmp_dir"])):
            part_path = os.path.join(info["tmp_dir"], part)
            with open(part_path, "rb") as pf:
                shutil.copyfileobj(pf, out)

    # bersihkan tmp
    shutil.rmtree(info["tmp_dir"], ignore_errors=True)

    return jsonify({
        "status": "ok",
        "file": final_filename
    })