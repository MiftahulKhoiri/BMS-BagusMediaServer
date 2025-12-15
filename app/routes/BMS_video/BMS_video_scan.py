# ============================================================================
# BMS_video_scan.py — Scan storage & import + AUTO THUMBNAIL
# - Multi-user safe
# - Thumbnail berbasis PATH video (global, shared)
# - Thumbnail dibuat saat scan (1x saja)
# ============================================================================

import os
import subprocess
import hashlib
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import PICTURES_FOLDER
from .BMS_video_db import get_db, is_video_file, current_user_identifier

# Blueprint
video_scan = Blueprint("video_scan", __name__, url_prefix="/video")

# ============================================================================
# Thumbnail folder
# ============================================================================
THUMBNAIL_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail")
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)


# ============================================================================
# Helper: nama thumbnail berbasis PATH video (GLOBAL)
# ============================================================================
def get_thumbnail_name(video_path):
    """
    Nama thumbnail konsisten berdasarkan PATH video
    Semua user mendapat thumbnail yang sama untuk video yang sama
    """
    key = os.path.abspath(video_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


# ============================================================================
# Helper: generate thumbnail dengan ffmpeg
# ============================================================================
def generate_thumbnail(video_path, thumbnail_path):
    """
    Ambil frame tengah video menggunakan ffmpeg
    Aman: tidak mengganggu scan jika gagal
    """
    try:
        # Ambil durasi video
        cmd_duration = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        duration = float(
            subprocess.check_output(cmd_duration).decode().strip()
        )
        middle = duration / 2

        # Generate thumbnail
        cmd_thumb = [
            "ffmpeg",
            "-ss", str(middle),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            thumbnail_path
        ]

        subprocess.run(
            cmd_thumb,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True

    except Exception:
        return False


# ============================================================================
# Scan storage (Android / Termux friendly)
# ============================================================================
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


# ============================================================================
# Route: scan & import DB + thumbnail
# ============================================================================
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

        row = cur.execute("""
            SELECT id FROM folders
            WHERE folder_path=? AND user_id=?
        """, (folder_path, owner)).fetchone()

        if row:
            folder_id = row["id"]
        else:
            try:
                cur.execute("""
                    INSERT INTO folders (folder_name, folder_path, user_id)
                    VALUES (?,?,?)
                """, (fn, folder_path, owner))
                folder_id = cur.lastrowid
                folders_new.append(fn)

            except Exception:
                row2 = cur.execute("""
                    SELECT id FROM folders
                    WHERE folder_path=? AND user_id=?
                """, (folder_path, owner)).fetchone()
                if row2:
                    folder_id = row2["id"]
                else:
                    alt_path = folder_path + "::" + owner
                    cur.execute("""
                        INSERT INTO folders (folder_name, folder_path, user_id)
                        VALUES (?,?,?)
                    """, (fn, alt_path, owner))
                    folder_id = cur.lastrowid
                    folders_new.append(fn)

        # ================================
        # Proses file video
        # ================================
        for vid in f["files"]:
            fp = os.path.join(folder_path, vid)

            exists = cur.execute("""
                SELECT id FROM videos
                WHERE filepath=? AND user_id=?
            """, (fp, owner)).fetchone()

            if exists:
                continue

            try:
                size = os.path.getsize(fp)
            except:
                size = 0

            added = datetime.utcnow().isoformat()

            cur.execute("""
                INSERT INTO videos (filename, filepath, folder_id, size, added_at, user_id)
                VALUES (?,?,?,?,?,?)
            """, (vid, fp, folder_id, size, added, owner))

            videos_new.append(vid)

            # ================================
            # AUTO GENERATE THUMBNAIL
            # ================================
            thumb_name = get_thumbnail_name(fp)
            thumb_path = os.path.join(THUMBNAIL_FOLDER, thumb_name)

            if not os.path.exists(thumb_path):
                generate_thumbnail(fp, thumb_path)

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "folders_added": folders_new,
        "videos_added": videos_new,
        "message": f"{len(folders_new)} folder dan {len(videos_new)} video baru."
    })