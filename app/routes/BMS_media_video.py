from flask import Blueprint, request, jsonify, Response, render_template
import os
from datetime import datetime
import mimetypes

video = Blueprint("video", __name__, url_prefix="/video")

BASE_PATH = os.path.abspath("storage")

if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)


# ================================
# HELPER: Amankan path
# ================================
def _resolve_path(rel):
    if rel is None:
        rel = ""
    rel = rel.strip().lstrip("/")
    target = os.path.abspath(os.path.join(BASE_PATH, rel))
    if not target.startswith(BASE_PATH):
        return None
    return target


# ================================
# HELPER: Metadata file
# ================================
def _file_info(abs_path):
    stat = os.stat(abs_path)
    return {
        "name": os.path.basename(abs_path),
        "path": os.path.relpath(abs_path, BASE_PATH).replace("\\", "/"),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


# ================================
# LIST VIDEO
# ================================
@video.route("/list")
def BMS_video_list():
    rel = request.args.get("path", "")
    target = _resolve_path(rel)

    if target is None or not os.path.exists(target):
        return jsonify({"error": "Path tidak ditemukan"}), 400

    items = os.listdir(target)

    extensions = (".mp4", ".mkv", ".webm", ".avi", ".mov")

    videos = [
        x for x in items if os.path.isfile(os.path.join(target, x)) and x.lower().endswith(extensions)
    ]

    videos_meta = []
    for v in videos:
        try:
            videos_meta.append(_file_info(os.path.join(target, v)))
        except:
            pass

    return jsonify({
        "path": rel,
        "videos": videos_meta
    })


# ================================
# STREAM VIDEO (WITH RANGE)
# ================================
def _video_partial_response(path, headers):
    file_size = os.path.getsize(path)
    range_header = headers.get("Range", None)

    if not range_header:
        # Tidak ada range → kirim full file
        return Response(open(path, "rb"), mimetype=mimetypes.guess_type(path)[0])

    try:
        range_val = range_header.split("=")[1]
        start_str, end_str = range_val.split("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
    except:
        return Response(status=416)

    if start > end or end >= file_size:
        return Response(status=416)

    length = end - start + 1

    with open(path, "rb") as f:
        f.seek(start)
        data = f.read(length)

    resp = Response(data, 206, mimetype=mimetypes.guess_type(path)[0])
    resp.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
    resp.headers.add("Accept-Ranges", "bytes")
    resp.headers.add("Content-Length", str(length))
    return resp


@video.route("/stream")
def BMS_video_stream():
    rel = request.args.get("path")
    target = _resolve_path(rel)

    if target is None or not os.path.isfile(target):
        return "File tidak ditemukan", 404

    return _video_partial_response(target, request.headers)


# ================================
# HALAMAN PLAYER
# ================================
@video.route("/player")
def BMS_video_player_page():
    return render_template("BMSvideo_player.html")