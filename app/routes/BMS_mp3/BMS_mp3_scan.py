# ============================================================================
#   BMS MP3 MODULE — SCAN STORAGE (PATH-BASED THUMBNAIL)
#   ✔ Scan storage (Android / Termux)
#   ✔ Import folder & track MP3
#   ✔ Thumbnail GLOBAL berbasis PATH (ID3 cover)
# ============================================================================

import os
import hashlib
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_mp3.BMS_mp3_cover import extract_cover
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import PICTURES_FOLDER
from .BMS_mp3_db import get_db, current_user_identifier, is_mp3

mp3_scan = Blueprint("mp3_scan", __name__, url_prefix="/mp3")

# ============================================================================
#   THUMBNAIL MP3 FOLDER
# ============================================================================
THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")
os.makedirs(THUMBNAIL_MP3_FOLDER, exist_ok=True)


# ============================================================================
#   HELPER: thumbnail name berbasis PATH (GLOBAL)
# ============================================================================
def get_mp3_thumbnail_name(mp3_path):
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


# ============================================================================
#   SCAN STORAGE
# ============================================================================
def scan_storage_for_mp3():
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")

    MAX_FOLDERS = 200
    MAX_FILES = 300

    folders = []
    used = 0

    for root, dirs, files in os.walk(ROOT):
        if used >= MAX_FOLDERS:
            break

        mp3s = [f for f in files if is_mp3(f)]
        if not mp3s:
            continue

        folders.append({
            "folder_path": root,
            "folder_name": os.path.basename(root) or root,
            "files": mp3s[:MAX_FILES]
        })

        used += 1

    return folders


# ============================================================================
#   ROUTE: SCAN + IMPORT
# ============================================================================
@mp3_scan.route("/scan-db", methods=["POST"])
def scan_db():
    username = session.get("username", "UNKNOWN")
    owner = current_user_identifier()

    BMS_write_log("SCAN MP3", username)

    folders = scan_storage_for_mp3()
    conn = get_db()
    cur = conn.cursor()

    folders_added = []
    tracks_added = []

    try:
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            row = cur.execute(
                "SELECT id FROM mp3_folders WHERE folder_path=?",
                (folder_path,)
            ).fetchone()

            if row:
                folder_id = row["id"]
            else:
                cur.execute(
                    "INSERT INTO mp3_folders (folder_name, folder_path) VALUES (?,?)",
                    (folder_name, folder_path)
                )
                folder_id = cur.lastrowid
                folders_added.append(folder_name)

            # ================================
            # PROSES FILE MP3
            # ================================
            for fn in f["files"]:
                fp = os.path.join(folder_path, fn)
                if not os.path.exists(fp):
                    continue

                exists = cur.execute("""
                    SELECT id FROM mp3_tracks
                    WHERE filepath=? AND user_id=?
                """, (fp, owner)).fetchone()

                if exists:
                    continue

                size = os.path.getsize(fp)
                added_at = datetime.utcnow().isoformat()

                cur.execute("""
                    INSERT INTO mp3_tracks
                    (folder_id, filename, filepath, size, added_at, user_id)
                    VALUES (?,?,?,?,?,?)
                """, (folder_id, fn, fp, size, added_at, owner))

                tracks_added.append(fn)

                # ================================
                # AUTO MP3 THUMBNAIL (ID3)
                # ================================
                thumb_name = get_mp3_thumbnail_name(fp)
                thumb_abs = os.path.join(THUMBNAIL_MP3_FOLDER, thumb_name)

                if not os.path.exists(thumb_abs):
                    try:
                        extract_cover(fp, thumb_abs)
                    except Exception:
                        pass  # silent & aman

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": folders_added,
        "tracks_added": tracks_added,
        "message": f"{len(folders_added)} folder dan {len(tracks_added)} MP3 baru."
    })