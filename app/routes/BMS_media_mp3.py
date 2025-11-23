from flask import Blueprint, request, jsonify, Response, send_file, render_template
from werkzeug.utils import safe_join
import os

mp3 = Blueprint("mp3", __name__, url_prefix="/mp3")

# Base folder tempat file media (samakan dengan filemanager)
BASE_PATH = os.path.abspath("storage")

if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)


# ---------------------------
# Helper: aman path resolve
# ---------------------------
def _resolve_path(rel_path):
    """
    Resolve relative path under BASE_PATH, cegah path traversal.
    Mengembalikan absolute path jika valid, atau None jika invalid.
    """
    if rel_path is None:
        rel_path = ""
    # normalisasi
    rel_path = rel_path.strip().lstrip("/")
    candidate = os.path.abspath(os.path.join(BASE_PATH, rel_path))
    # Pastikan masih di dalam BASE_PATH
    if not candidate.startswith(BASE_PATH):
        return None
    return candidate


# ---------------------------
# Helper: basic metadata
# ---------------------------
def _file_info(abs_path):
    stat = os.stat(abs_path)
    return {
        "name": os.path.basename(abs_path),
        "path": os.path.relpath(abs_path, BASE_PATH).replace("\\", "/"),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


# ---------------------------
# LIST MP3
# ---------------------------
@mp3.route("/list")
def BMS_mp3_list():
    """
    GET /mp3/list?path=folder/subfolder
    Returns JSON with lists of folders and mp3 files (metadata).
    """
    rel = request.args.get("path", "")
    target = _resolve_path(rel)
    if target is None or not os.path.exists(target):
        return jsonify({"error": "Path tidak ditemukan"}), 400

    items = os.listdir(target)
    folders = [x for x in items if os.path.isdir(os.path.join(target, x))]
    files = [x for x in items if os.path.isfile(os.path.join(target, x)) and x.lower().endswith(".mp3")]

    files_meta = []
    for f in files:
        try:
            files_meta.append(_file_info(os.path.join(target, f)))
        except:
            pass

    return jsonify({
        "path": rel,
        "folders": folders,
        "mp3_files": files_meta
    })


# ---------------------------
# METADATA SINGLE FILE
# ---------------------------
@mp3.route("/meta")
def BMS_mp3_meta():
    """
    GET /mp3/meta?path=folder/file.mp3
    """
    rel = request.args.get("path")
    target = _resolve_path(rel)
    if target is None or not os.path.isfile(target):
        return jsonify({"error": "File tidak ditemukan"}), 404

    return jsonify(_file_info(target))


# ---------------------------
# STREAM SUPPORTING RANGE
# ---------------------------
def _partial_response(path, request_headers):
    """
    Mengembalikan response yang mendukung Range header (byte serving).
    """
    file_size = os.path.getsize(path)
    range_header = request_headers.get('Range', None)
    if not range_header:
        # Tidak ada range: kirim seluruh file
        return send_file(path, as_attachment=False, mimetype='audio/mpeg')

    # Parse Range header: "bytes=start-end"
    try:
        range_val = range_header.strip().split('=')[1]
        start_str, end_str = range_val.split('-')
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
    except Exception:
        # Jika parsing gagal, kirim seluruh file
        return send_file(path, as_attachment=False, mimetype='audio/mpeg')

    if start > end or end >= file_size:
        # invalid range
        return Response(status=416)

    length = end - start + 1
    with open(path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    rv = Response(data, 206, mimetype='audio/mpeg', direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv


@mp3.route("/stream")
def BMS_mp3_stream():
    """
    GET /mp3/stream?path=folder/file.mp3
    Supports Range header for seeking.
    """
    rel = request.args.get("path")
    target = _resolve_path(rel)
    if target is None or not os.path.isfile(target):
        return "File tidak ditemukan", 404

    # Pastikan file mp3
    if not target.lower().endswith(".mp3"):
        return "Bukan file MP3", 400

    return _partial_response(target, request.headers)


# ---------------------------
# SIMPLE PLAYER PAGE (OPTIONAL)
# ---------------------------
@mp3.route("/player")
def BMS_mp3_player_page():
    """
    Halaman sederhana untuk memutar file MP3 dari storage.
    Contoh pemanggilan JS: /mp3/list?path=...
    """
    return render_template("BMSmp3_player.html")