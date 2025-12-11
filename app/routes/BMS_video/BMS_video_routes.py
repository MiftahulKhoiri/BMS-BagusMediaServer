# ============================================================================
# BMS_video_routes.py — Routes untuk UI & API list/play/delete (owner-scoped)
# - No forced login on page view (page accessible)
# - List endpoints filtered by owner
# ============================================================================

from flask import Blueprint, jsonify, render_template, request, Response
from .BMS_video_db import get_db, current_user_identifier, is_inside_video_folder
import os

video_routes = Blueprint("video_routes", __name__, url_prefix="/video")


@video_routes.route("/")
def page_video():
    # Page is accessible without forcing login; frontend may ask user to login if needed
    return render_template("BMS_video.html")


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
    return jsonify([dict(r) for r in rows])


@video_routes.route("/play/<int:video_id>")
def play_video(video_id):
    owner = current_user_identifier()
    conn = get_db()
    row = conn.execute("SELECT filepath, user_id FROM videos WHERE id=?", (video_id,)).fetchone()
    conn.close()
    if not row:
        return "Video tidak ditemukan", 404
    if str(row["user_id"]) != str(owner):
        return "Akses ditolak", 403

    fp = row["filepath"]
    if not os.path.exists(fp):
        return "File hilang", 404

    # Range support simple implementation (optional to improve)
    range_hdr = request.headers.get("Range")
    if not range_hdr:
        return Response(open(fp, "rb").read(), mimetype="video/mp4")

    # fallback: simple partial response (works for most players)
    try:
        size = os.path.getsize(fp)
        parts = range_hdr.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else size - 1
        length = end - start + 1
        with open(fp, "rb") as f:
            f.seek(start)
            data = f.read(length)
        resp = Response(data, 206, mimetype="video/mp4")
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(length))
        return resp
    except Exception as e:
        return Response(open(fp, "rb").read(), mimetype="video/mp4")