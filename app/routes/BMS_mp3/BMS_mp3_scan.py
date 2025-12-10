# ============================================================================
#   BMS MP3 MODULE — SCAN STORAGE (FINAL)
#   Bagian ini mengelola:
#     ✔ Scan seluruh storage (Android / Termux compatible)
#     ✔ Import folder ke DB
#     ✔ Import track MP3 per-user
# ============================================================================

import os
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from .BMS_mp3_db import get_db, current_user_identifier, is_mp3

mp3_scan = Blueprint("mp3_scan", __name__, url_prefix="/mp3")


# ============================================================================
#   SCAN STORAGE
# ============================================================================
def scan_storage_for_mp3():
    """
    Scan folder Android:
      ✔ /storage/emulated/0
      ✔ fallback → HOME Termux
    """
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")  # Termux

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

    BMS_write_log("Memulai scan MP3", username)

    folders = scan_storage_for_mp3()

    conn = get_db()
    cur = conn.cursor()

    folders_added = []
    tracks_added = []

    try:
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            # simpan folder
            row = cur.execute(
                "SELECT id FROM mp3_folders WHERE folder_path=?", (folder_path,)
            ).fetchone()

            if row:
                folder_id = row["id"]
            else:
                cur.execute("""
                    INSERT INTO mp3_folders (folder_name, folder_path)
                    VALUES (?,?)
                """, (folder_name, folder_path))
                folder_id = cur.lastrowid
                folders_added.append(folder_name)

            # simpan track
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
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (folder_id, fn, fp, size, added_at, owner))

                tracks_added.append(fn)

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
        "message": f"{len(folders_added)} folder dan {len(tracks_added)} MP3 ditemukan."
    })