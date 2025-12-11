# ============================================================================
#   BMS VIDEO SCAN — FINAL (Multi-user, No Login Block)
# ============================================================================

import os
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from .BMS_video_db import (
    get_db,
    is_video_file,
    current_user_identifier
)

video_scan = Blueprint("video_scan", __name__, url_prefix="/video")


def scan_storage_for_video():
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")

    MAX_FOLDERS = 200
    MAX_FILES = 300
    found = []

    for root, dirs, files in os.walk(ROOT):
        if len(found) >= MAX_FOLDERS:
            break

        vids = [f for f in files if is_video_file(f)]
        if not vids:
            continue

        found.append({
            "folder_path": root,
            "folder_name": os.path.basename(root) or root,
            "files": vids[:MAX_FILES]
        })

    return found


@video_scan.route("/scan-db", methods=["POST"])
def scan_db():
    owner = current_user_identifier()
    username = session.get("username", owner)

    BMS_write_log(f"SCAN VIDEO oleh: {owner}", username)

    folders = scan_storage_for_video()

    conn = get_db()
    cur = conn.cursor()

    folders_new = []
    videos_new = []

    for f in folders:
        folder_path = f["folder_path"]
        fn = f["folder_name"]

        # Cari folder user
        row = cur.execute("""
            SELECT id FROM folders
            WHERE folder_path=? AND user_id=?
        """, (folder_path, owner)).fetchone()

        if row:
            folder_id = row["id"]
        else:
            cur.execute("""
                INSERT INTO folders (folder_name, folder_path, user_id)
                VALUES (?,?,?)
            """, (fn, folder_path, owner))
            folder_id = cur.lastrowid
            folders_new.append(fn)

        for vid in f["files"]:
            fp = os.path.join(folder_path, vid)

            exists = cur.execute("""
                SELECT id FROM videos
                WHERE filepath=? AND user_id=?
            """, (fp, owner)).fetchone()

            if exists:
                continue

            size = os.path.getsize(fp)
            added = datetime.utcnow().isoformat()

            cur.execute("""
                INSERT INTO videos (filename, filepath, folder_id, size, added_at, user_id)
                VALUES (?,?,?,?,?,?)
            """, (vid, fp, folder_id, size, added, owner))

            videos_new.append(vid)

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": folders_new,
        "videos_added": videos_new,
        "message": f"{len(folders_new)} folder dan {len(videos_new)} video baru."
    })