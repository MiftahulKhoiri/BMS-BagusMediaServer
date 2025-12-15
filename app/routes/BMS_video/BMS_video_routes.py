# ============================================================================
# BMS_video_routes.py — Routes untuk UI & API list/play/delete (owner-scoped)
# - No forced login on page view (page accessible)
# - List endpoints filtered by owner
# - Thumbnail support (PATH-based, shared)
# ============================================================================

import os
import hashlib
from flask import (
    Blueprint, jsonify, render_template,
    request, Response, send_from_directory
)

from app.BMS_config import PICTURES_FOLDER
from .BMS_video_db import (
    get_db, current_user_identifier, is_inside_video_folder
)

# Membuat Blueprint untuk rute video dengan prefix '/video'
video_routes = Blueprint("video_routes", __name__, url_prefix="/video")

# ============================================================================
# Thumbnail folder
# ============================================================================
THUMBNAIL_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail")


# ============================================================================
# Helper: hitung nama thumbnail berbasis PATH video
# HARUS SAMA dengan yang ada di BMS_video_scan.py
# ============================================================================
def get_thumbnail_name(video_path):
    key = os.path.abspath(video_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


# ============================================================================
# Page utama
# ============================================================================
@video_routes.route("/")
def page_video():
    return render_template("BMS_video.html")


# ============================================================================
# Serve thumbnail
# ============================================================================
@video_routes.route("/thumbnail/<name>")
def serve_thumbnail(name):
    return send_from_directory(
        THUMBNAIL_FOLDER,
        name,
        as_attachment=False
    )


# ============================================================================
# List folder video (owner scoped)
# ============================================================================
@video_routes.route("/folders")
def list_folders():
    owner = current_user_identifier()
    conn = get_db()

    rows = conn.execute("""
        SELECT id, folder_name, folder_path,
               (SELECT COUNT(*) FROM videos v
                WHERE v.folder_id = folders.id AND v.user_id=?)
               AS total_video
        FROM folders
        WHERE user_id=?
        ORDER BY folder_name ASC
    """, (owner, owner)).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================================
# List video dalam folder + thumbnail
# ============================================================================
@video_routes.route("/folder/<int:folder_id>/videos")
def list_videos(folder_id):
    owner = current_user_identifier()
    conn = get_db()

    rows = conn.execute("""
        SELECT id, filename, filepath, size, added_at
        FROM videos
        WHERE folder_id=? AND user_id=?
        ORDER BY filename ASC
    """, (folder_id, owner)).fetchall()

    conn.close()

    videos = []
    for r in rows:
        thumb = get_thumbnail_name(r["filepath"])
        videos.append({
            "id": r["id"],
            "filename": r["filename"],
            "filepath": r["filepath"],
            "size": r["size"],
            "added_at": r["added_at"],
            "thumbnail": thumb
        })

    return jsonify(videos)


# ============================================================================
# Stream video (support Range / seek)
# ============================================================================
@video_routes.route("/play/<int:video_id>")
def play_video(video_id):
    owner = current_user_identifier()
    conn = get_db()

    row = conn.execute("""
        SELECT filepath, user_id
        FROM videos
        WHERE id=? AND user_id=?
    """, (video_id, owner)).fetchone()

    conn.close()

    if not row:
        return "Video tidak ditemukan", 404

    fp = row["filepath"].split("::user::")[0]

    if not os.path.exists(fp):
        return "File fisik hilang", 404

    size = os.path.getsize(fp)
    range_header = request.headers.get("Range")

    if not range_header:
        return Response(open(fp, "rb").read(), mimetype="video/mp4")

    parts = range_header.replace("bytes=", "").split("-")
    start = int(parts[0]) if parts[0] else 0
    end = int(parts[1]) if len(parts) > 1 and parts[1] else size - 1
    length = end - start + 1

    with open(fp, "rb") as f:
        f.seek(start)
        data = f.read(length)

    resp = Response(data, 206, mimetype="video/mp4")
    resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
    resp.headers.add("Accept-Ranges", "bytes")
    resp.headers.add("Content-Length", str(length))
    return resp


# ============================================================================
# Watch page
# ============================================================================
@video_routes.route("/watch/<int:video_id>")
def video_watch(video_id):
    owner = current_user_identifier()
    conn = get_db()

    row = conn.execute("""
        SELECT id, filename, folder_id, filepath, user_id
        FROM videos
        WHERE id=? AND user_id=?
    """, (video_id, owner)).fetchone()

    conn.close()

    if not row:
        return "Video tidak ditemukan / akses ditolak", 404

    return render_template(
        "BMS_video_play.html",
        video_id=row["id"],
        filename=row["filename"],
        folder_id=row["folder_id"]
    )