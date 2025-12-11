# ============================================================================
#   BMS VIDEO ROUTES — FINAL (Multi-user, No Login Block)
# ============================================================================

import os
from flask import Blueprint, jsonify, render_template
from .BMS_video_db import (
    get_db,
    current_user_identifier,
    is_inside_video_folder
)

video_routes = Blueprint("video_routes", __name__, url_prefix="/video")


@video_routes.route("/")
def page_video():
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