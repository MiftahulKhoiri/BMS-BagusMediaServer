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

from BMS_mp3_cover import extract_cover
from app.routes.BMS_logger import BMS_write_log
from .BMS_mp3_db import get_db, current_user_identifier, is_mp3

# Membuat Blueprint untuk rute pemindaian MP3 dengan prefix '/mp3'
mp3_scan = Blueprint("mp3_scan", __name__, url_prefix="/mp3")


# ============================================================================
#   SCAN STORAGE
# ============================================================================
def scan_storage_for_mp3():
    """
    Memindai seluruh penyimpanan perangkat untuk mencari file MP3.
    
    Fungsi ini dirancang untuk kompatibel dengan lingkungan Android/Termux:
    1. Prioritas: /storage/emulated/0 (penyimpanan internal Android)
    2. Fallback: Home directory Termux (~/) jika folder Android tidak ada
    
    Fungsi ini membatasi jumlah folder dan file yang dipindai untuk menghindari
    pemindaian yang terlalu lama atau penggunaan memori berlebihan.
    
    Returns:
        list: Daftar dictionary yang berisi informasi folder dan file MP3 di dalamnya
    """
    # Tentukan root directory berdasarkan platform
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")  # Fallback untuk Termux

    # Batasan untuk mencegah pemindaian tak terbatas
    MAX_FOLDERS = 200  # Maksimal folder yang akan dipindai
    MAX_FILES = 300    # Maksimal file per folder yang akan diproses

    folders = []
    used = 0

    # Rekursif walk melalui direktori
    for root, dirs, files in os.walk(ROOT):
        # Hentikan jika sudah mencapai batas maksimal folder
        if used >= MAX_FOLDERS:
            break

        # Filter hanya file MP3 dari daftar file
        mp3s = [f for f in files if is_mp3(f)]
        
        # Lewati folder jika tidak ada file MP3
        if not mp3s:
            continue

        # Simpan informasi folder dan file MP3 di dalamnya
        folders.append({
            "folder_path": root,                    # Path lengkap folder
            "folder_name": os.path.basename(root) or root,  # Nama folder (atau path jika kosong)
            "files": mp3s[:MAX_FILES]               # File MP3 (dibatasi jumlahnya)
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

                # INSERT TRACK
                cur.execute("""
                    INSERT INTO mp3_tracks
                    (folder_id, filename, filepath, size, added_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (folder_id, fn, fp, size, added_at, owner))

                track_id = cur.lastrowid
                tracks_added.append(fn)

                # ⭐ COVER: extract dari ID3 (aman & silent)
                cover_rel = f"/static/mp3_cover/tracks/{track_id}.jpg"
                cover_abs = f"static/mp3_cover/tracks/{track_id}.jpg"

                try:
                    ok = extract_cover(fp, cover_abs)
                    if ok:
                        cur.execute(
                            "UPDATE mp3_tracks SET cover_path=? WHERE id=?",
                            (cover_rel, track_id)
                        )
                except Exception:
                    pass  # cover gagal? tidak masalah, lanjut

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