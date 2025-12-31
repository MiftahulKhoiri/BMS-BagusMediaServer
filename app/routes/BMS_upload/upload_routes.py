import os
import uuid
import time
import shutil

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from .upload_auth import fm_auth
from .upload_paths import UPLOAD_INTERNAL, internal_path
from .upload_sessions import upload_lock, upload_sessions
from .upload_utils import check_disk_space

upload = Blueprint("upload", __name__, url_prefix="/upload")

# =================================================
# START SESSION
# =================================================
@upload.route("/upload_chunk/start", methods=["POST"])
@fm_auth
def upload_start():
    filename = secure_filename(request.form.get("name", ""))
    total_size = int(request.form.get("total_size", 0))

    if not filename or total_size <= 0:
        return jsonify({"error": "Data tidak valid"}), 400

    if not check_disk_space(total_size):
        return jsonify({"error": "Disk penuh"}), 507

    session_id = uuid.uuid4().hex
    tmp_dir = os.path.join(UPLOAD_INTERNAL, session_id)
    os.makedirs(tmp_dir, exist_ok=True)

    with upload_lock:
        upload_sessions[session_id] = {
            "filename": filename,
            "total": total_size,
            "received": 0,
            "tmp_dir": tmp_dir,
            "created": time.time()
        }

    return jsonify({"session_id": session_id})


# =================================================
# APPEND CHUNK
# =================================================
@upload.route("/upload_chunk/append", methods=["POST"])
@fm_auth
def upload_append():
    session_id = request.form.get("session_id")
    chunk_index = request.form.get("chunk_index")
    chunk = request.files.get("chunk")

    if not session_id or chunk is None:
        return jsonify({"error": "Chunk tidak valid"}), 400

    with upload_lock:
        info = upload_sessions.get(session_id)

    if not info:
        return jsonify({"error": "Session tidak ditemukan"}), 404

    part_name = f"{int(chunk_index):06d}.part"
    part_path = os.path.join(info["tmp_dir"], part_name)
    chunk.save(part_path)

    size = os.path.getsize(part_path)

    with upload_lock:
        info["received"] += size
        progress = int((info["received"] / info["total"]) * 100)

    return jsonify({"progress": min(progress, 100)})


# =================================================
# FINISH UPLOAD
# =================================================
@upload.route("/upload_chunk/finish", methods=["POST"])
@fm_auth
def upload_finish():
    session_id = request.form.get("session_id")
    final_filename = secure_filename(request.form.get("final_filename", ""))

    if not session_id or not final_filename:
        return jsonify({"error": "Finish tidak valid"}), 400

    with upload_lock:
        info = upload_sessions.pop(session_id, None)

    if not info:
        return jsonify({"error": "Session tidak ditemukan"}), 404

    final_path = internal_path(final_filename)

    with open(final_path, "wb") as out:
        for part in sorted(os.listdir(info["tmp_dir"])):
            with open(os.path.join(info["tmp_dir"], part), "rb") as pf:
                shutil.copyfileobj(pf, out)

    shutil.rmtree(info["tmp_dir"], ignore_errors=True)

    return jsonify({"status": "ok", "file": final_filename})