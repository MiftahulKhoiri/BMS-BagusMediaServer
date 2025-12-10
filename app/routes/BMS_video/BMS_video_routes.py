# ============================================================================
#   BMS VIDEO MODULE — MAIN ROUTES
# ============================================================================

import os
from flask import Blueprint, jsonify, request, Response, render_template

from .BMS_video_db import (
    get_db,
    video_login_required,
    is_inside_video_folder,
)

video_routes = Blueprint("video_routes", __name__, url_prefix="/video")


# ============================================================================
#   VIDEO PAGE
# ============================================================================
@video_routes.route("/")
def page_video():
    return render_template("BMS_video.html")


# ============================================================================
#   LIST FOLDERS
# ============================================================================
@video_routes.route("/folders")
def folders():
    conn = get_db()
    rows = conn.execute("""
        SELECT folders.id, folders.folder_name, folders.folder_path,
               COUNT(videos.id) AS total_video
        FROM folders
        LEFT JOIN videos ON videos.folder_id = folders.id
        GROUP BY folders.id
        ORDER BY folder_name ASC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================================
#   LIST VIDEOS IN FOLDER
# ============================================================================
@video_routes.route("/folder/<int:folder_id>/videos")
def list_videos(folder_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT id, filename, filepath, size, added_at
        FROM videos
        WHERE folder_id=?
        ORDER BY filename ASC
    """, (folder_id,)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ============================================================================
#   STREAM VIDEO WITH RANGE SUPPORT
# ============================================================================
def parse_range_header(path):
    header = request.headers.get("Range")
    if not header:
        return None

    try:
        size = os.path.getsize(path)
        parts = header.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else size - 1
        return start, end, size
    except:
        return None


@video_routes.route("/play/<int:video_id>")
def play_video(video_id):
    conn = get_db()
    row = conn.execute("SELECT filepath FROM videos WHERE id=?", (video_id,)).fetchone()
    conn.close()

    if not row:
        return "Video tidak ditemukan", 404

    fp = row["filepath"]

    if not os.path.exists(fp):
        return "File tidak ditemukan", 404

    if not is_inside_video_folder(fp):
        return jsonify({"error": "Akses path dilarang!"}), 403

    # Range streaming
    r = parse_range_header(fp)
    if r:
        start, end, size = r
        chunk = end - start + 1

        with open(fp, "rb") as f:
            f.seek(start)
            data = f.read(chunk)

        resp = Response(data, 206, mimetype="video/mp4")
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(chunk))
        return resp

    # normal mode
    return Response(open(fp, "rb").read(), mimetype="video/mp4")


# ============================================================================
#   DELETE VIDEO
# ============================================================================
@video_routes.route("/delete/<int:video_id>", methods=["POST"])
def delete_video(video_id):
    conn = get_db()
    conn.execute("DELETE FROM videos WHERE id=?", (video_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "message": "Video telah dihapus"})


# ============================================================================
#   WATCH PAGE
# ============================================================================
@video_routes.route("/watch/<int:video_id>")
def watch_video(video_id):
    conn = get_db()
    row = conn.execute("""
        SELECT id, filename, folder_id
        FROM videos
        WHERE id=?
    """, (video_id,)).fetchone()
    conn.close()

    if not row:
        return "Video tidak ditemukan", 404

    return render_template(
        "BMS_video_play.html",
        video_id=row["id"],
        filename=row["filename"],
        folder_id=row["folder_id"]
    )