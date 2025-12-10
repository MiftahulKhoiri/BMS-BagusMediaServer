# ============================================================================
#   BMS VIDEO MODULE — SCAN & IMPORT STORAGE
# ============================================================================

import os
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from .BMS_video_db import get_db, is_video_file, video_login_required

video_scan = Blueprint("video_scan", __name__)


# ============================================================================
#   SCAN STORAGE FOR VIDEO
# ============================================================================
def scan_storage_for_video():
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")  # Termux fallback

    MAX_FOLDERS = 200
    MAX_FILES = 300

    folders = []
    used = 0

    for root, dirs, files in os.walk(ROOT):

        if used >= MAX_FOLDERS:
            break

        vids = [f for f in files if is_video_file(f)]
        if not vids:
            continue

        folders.append({
            "folder_path": root,
            "folder_name": os.path.basename(root) or root,
            "files": vids[:MAX_FILES]
        })

        used += 1

    return folders


# ============================================================================
#   ROUTE: SCAN + IMPORT
# ============================================================================
@video_scan.route("/video/scan-db", methods=["POST"])
def scan_db():
    if not video_login_required():
        return jsonify({"error": "Belum login"}), 403

    username = session.get("username", "UNKNOWN")
    BMS_write_log("Memulai scan video", username)

    folders = scan_storage_for_video()

    conn = get_db()
    cur = conn.cursor()

    folders_added = []
    videos_added = []

    try:
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            # Save folder
            row = cur.execute(
                "SELECT id FROM folders WHERE folder_path=?",
                (folder_path,)
            ).fetchone()

            if row:
                folder_id = row["id"]
            else:
                cur.execute("""
                    INSERT INTO folders (folder_name, folder_path)
                    VALUES (?,?)
                """, (folder_name, folder_path))
                folder_id = cur.lastrowid
                folders_added.append(folder_name)

            # Save videos
            for vid in f["files"]:
                fp = os.path.join(folder_path, vid)

                if not os.path.exists(fp):
                    continue

                exists = cur.execute(
                    "SELECT id FROM videos WHERE filepath=?",
                    (fp,)
                ).fetchone()

                if exists:
                    continue

                size = os.path.getsize(fp)
                added = datetime.utcnow().isoformat()

                cur.execute("""
                    INSERT INTO videos (filename, filepath, folder_id, size, added_at)
                    VALUES (?,?,?,?,?)
                """, (vid, fp, folder_id, size, added))

                videos_added.append(vid)

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": folders_added,
        "videos_added": videos_added
    })