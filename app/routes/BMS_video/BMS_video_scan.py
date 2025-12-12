# ============================================================================
# BMS_video_scan.py — Scan storage & import (Multi-user, no login block)
# - Safe insert (try/except) to avoid UNIQUE crashes
# - Inserts folder + videos under owner (current_user_identifier)
# ============================================================================

import os
from datetime import datetime
from flask import Blueprint, jsonify, session

from app.routes.BMS_logger import BMS_write_log
from .BMS_video_db import get_db, is_video_file, current_user_identifier

# Membuat Blueprint untuk rute pemindaian video dengan prefix '/video'
video_scan = Blueprint("video_scan", __name__, url_prefix="/video")


def scan_storage_for_video():
    """
    Memindai penyimpanan perangkat untuk mencari file video.
    
    Fungsi ini membatasi jumlah folder dan file yang dipindai untuk menghindari
    proses yang terlalu lama. Didesain untuk kompatibel dengan Android/Termux.
    
    Returns:
        list: Daftar dictionary berisi informasi folder dan file video di dalamnya
    """
    # Tentukan root directory berdasarkan platform
    ROOT = "/storage/emulated/0"
    if not os.path.exists(ROOT):
        ROOT = os.path.expanduser("~")  # Fallback untuk Termux

    # Batasan untuk mencegah pemindaian tak terbatas
    MAX_FOLDERS = 200  # Maksimal folder yang akan dipindai
    MAX_FILES = 300    # Maksimal file per folder yang akan diproses
    found = []

    # Rekursif walk melalui direktori
    for root, dirs, files in os.walk(ROOT):
        # Hentikan jika sudah mencapai batas maksimal folder
        if len(found) >= MAX_FOLDERS:
            break

        # Filter hanya file video dari daftar file
        vids = [f for f in files if is_video_file(f)]
        
        # Lewati folder jika tidak ada file video
        if not vids:
            continue

        # Simpan informasi folder dan file video di dalamnya
        found.append({
            "folder_path": root,                    # Path lengkap folder
            "folder_name": os.path.basename(root) or root,  # Nama folder (atau path jika kosong)
            "files": vids[:MAX_FILES]               # File video (dibatasi jumlahnya)
        })

    return found


@video_scan.route("/scan-db", methods=["POST"])
def scan_db():
    """
    Endpoint untuk memindai penyimpanan dan mengimpor file video ke database.
    
    Proses:
    1. Memindai seluruh penyimpanan untuk mencari folder berisi video
    2. Menyimpan informasi folder ke tabel folders (jika belum ada untuk user ini)
    3. Menyimpan informasi video ke tabel videos (jika belum ada untuk user ini)
    
    Setiap folder dan video yang diimpor dikaitkan dengan owner (user yang sedang aktif).
    
    Returns:
        JSON response berisi status, jumlah folder dan video yang ditambahkan,
        atau pesan error jika terjadi masalah
    """
    # Ambil identifier user yang sedang aktif
    owner = current_user_identifier()
    # Ambil username untuk logging (gunakan owner sebagai fallback)
    username = session.get("username", owner)

    # Log awal proses pemindaian
    BMS_write_log(f"SCAN VIDEO oleh: {owner}", username)

    # Panggil fungsi pemindaian untuk mendapatkan daftar folder
    folders = scan_storage_for_video()

    conn = get_db()
    cur = conn.cursor()

    # Variabel untuk melacak apa yang telah ditambahkan
    folders_new = []  # Nama folder yang baru ditambahkan ke database
    videos_new = []   # Nama file video yang baru ditambahkan ke database

    # Proses setiap folder yang ditemukan
    for f in folders:
        folder_path = f["folder_path"]
        fn = f["folder_name"]

        # Cek apakah folder sudah ada di database untuk user ini
        row = cur.execute("""
            SELECT id FROM folders
            WHERE folder_path=? AND user_id=?
        """, (folder_path, owner)).fetchone()

        # Jika folder sudah ada, gunakan ID-nya
        if row:
            folder_id = row["id"]
        else:
            # Jika folder belum ada, coba insert dengan error handling
            try:
                cur.execute("""
                    INSERT INTO folders (folder_name, folder_path, user_id)
                    VALUES (?,?,?)
                """, (fn, folder_path, owner))
                folder_id = cur.lastrowid
                folders_new.append(fn)

            except Exception:
                # Fallback: coba lagi ambil ID folder jika insert gagal karena constraint
                row2 = cur.execute("""
                    SELECT id FROM folders
                    WHERE folder_path=? AND user_id=?
                """, (folder_path, owner)).fetchone()
                if row2:
                    folder_id = row2["id"]
                else:
                    # Kasus sangat langka: folder_path ada secara global tapi tidak untuk owner ini
                    # Buat path alternatif dengan menambahkan suffix owner untuk menghindari conflict
                    # Catatan: Branch ini defensif; normalnya idx_folders_path_user mencegah collision.
                    alt_path = folder_path + "::" + owner
                    cur.execute("""
                        INSERT INTO folders (folder_name, folder_path, user_id)
                        VALUES (?,?,?)
                    """, (fn, alt_path, owner))
                    folder_id = cur.lastrowid
                    folders_new.append(fn)

        # Simpan video untuk folder ini (scoped oleh owner)
        for vid in f["files"]:
            fp = os.path.join(folder_path, vid)

            # Cek apakah video sudah ada di database untuk user ini
            exists = cur.execute("""
                SELECT id FROM videos
                WHERE filepath=? AND user_id=?
            """, (fp, owner)).fetchone()

            # Jika sudah ada, skip
            if exists:
                continue

            # Dapatkan ukuran file (dengan error handling)
            try:
                size = os.path.getsize(fp)
            except:
                size = 0

            # Timestamp saat ini
            added = datetime.utcnow().isoformat()

            # Insert video ke database
            cur.execute("""
                INSERT INTO videos (filename, filepath, folder_id, size, added_at, user_id)
                VALUES (?,?,?,?,?,?)
            """, (vid, fp, folder_id, size, added, owner))

            videos_new.append(vid)

    # Commit perubahan ke database
    conn.commit()
    conn.close()

    # Return hasil pemindaian dan impor
    return jsonify({
        "status": "ok",
        "folders_added": folders_new,
        "videos_added": videos_new,
        "message": f"{len(folders_new)} folder dan {len(videos_new)} video baru."
    })