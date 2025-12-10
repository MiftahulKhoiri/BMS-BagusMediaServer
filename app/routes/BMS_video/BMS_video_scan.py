# ============================================================================
#   BMS VIDEO MODULE — SCAN STORAGE (FINAL PER-USER)
# ============================================================================

import os
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from .BMS_video_db import (
    get_db,
    is_video_file,
    current_user_identifier,
    video_login_required
)

# Prefix video tetap /video
video_scan = Blueprint("video_scan", __name__, url_prefix="/video")


# ============================================================================
#   SCAN STORAGE
# ============================================================================
def scan_storage_for_video():
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")  # Termux

    MAX_FOLDERS = 200
    MAX_FILES = 300

    result = []
    count = 0

    for root, dirs, files in os.walk(ROOT):
        if count >= MAX_FOLDERS:
            break

        vids = [f for f in files if is_video_file(f)]
        if not vids:
            continue

        result.append({
            "folder_path": root,
            "folder_name": os.path.basename(root) or root,
            "files": vids[:MAX_FILES]
        })

        count += 1

    return result


# ============================================================================
#   API: SCAN VIDEO & IMPORT PER-USER
# ============================================================================
@video_scan.route("/scan-db", methods=["POST"])
def scan_db():

    if not video_login_required():
        return jsonify({"error": "Belum login"}), 403

    owner = current_user_identifier()
    username = session.get("username", "UNKNOWN")

    BMS_write_log(f"Scan video milik user: {owner}", username)

    folders = scan_storage_for_video()

    conn = get_db()
    cur = conn.cursor()

    folders_added = []
    videos_added = []

    try:
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            # cek folder user
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
                """, (folder_name, folder_path, owner))
                folder_id = cur.lastrowid
                folders_added.append(folder_name)

            # simpan video milik user
            for vid in f["files"]:
                fp = os.path.join(folder_path, vid)

                if not os.path.exists(fp):
                    continue

                exists = cur.execute("""
                    SELECT id FROM videos
                    WHERE filepath=? AND user_id=?
                """, (fp, owner)).fetchone()

                if exists:
                    continue

                size = os.path.getsize(fp)
                added_at = datetime.utcnow().isoformat()

                cur.execute("""
                    INSERT INTO videos (filename, filepath, folder_id, size, added_at, user_id)
                    VALUES (?,?,?,?,?,?)
                """, (vid, fp, folder_id, size, added_at, owner))

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