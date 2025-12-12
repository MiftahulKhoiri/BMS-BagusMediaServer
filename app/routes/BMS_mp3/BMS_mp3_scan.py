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
    """
    Endpoint untuk memindai penyimpanan dan mengimpor file MP3 ke database.
    
    Proses:
    1. Memindai seluruh penyimpanan untuk mencari folder berisi MP3
    2. Menyimpan informasi folder ke tabel mp3_folders (jika belum ada)
    3. Menyimpan informasi track ke tabel mp3_tracks (jika belum ada)
    
    Setiap track yang diimpor dikaitkan dengan user yang sedang login.
    
    Returns:
        JSON response berisi status, jumlah folder dan track yang ditambahkan,
        atau pesan error jika terjadi masalah
    """
    # Ambil informasi user dari session untuk logging
    username = session.get("username", "UNKNOWN")
    # Ambil identifier user untuk kepemilikan track
    owner = current_user_identifier()

    # Log awal proses pemindaian
    BMS_write_log("Memulai scan MP3", username)

    # Panggil fungsi pemindaian untuk mendapatkan daftar folder
    folders = scan_storage_for_mp3()

    conn = get_db()
    cur = conn.cursor()

    # Variabel untuk melacak apa yang telah ditambahkan
    folders_added = []  # Nama folder yang baru ditambahkan ke database
    tracks_added = []   # Nama file MP3 yang baru ditambahkan ke database

    try:
        # Proses setiap folder yang ditemukan
        for f in folders:
            folder_path = f["folder_path"]
            folder_name = f["folder_name"]

            # Cek apakah folder sudah ada di database
            row = cur.execute(
                "SELECT id FROM mp3_folders WHERE folder_path=?", (folder_path,)
            ).fetchone()

            # Jika folder sudah ada, gunakan ID-nya
            if row:
                folder_id = row["id"]
            else:
                # Jika folder belum ada, tambahkan ke database
                cur.execute("""
                    INSERT INTO mp3_folders (folder_name, folder_path)
                    VALUES (?,?)
                """, (folder_name, folder_path))
                folder_id = cur.lastrowid
                folders_added.append(folder_name)

            # Proses setiap file MP3 dalam folder
            for fn in f["files"]:
                fp = os.path.join(folder_path, fn)

                # Skip jika file tidak ada (untuk berjaga-jaga)
                if not os.path.exists(fp):
                    continue

                # Cek apakah track sudah ada di database untuk user ini
                exists = cur.execute("""
                    SELECT id FROM mp3_tracks
                    WHERE filepath=? AND user_id=?
                """, (fp, owner)).fetchone()

                # Jika sudah ada, skip
                if exists:
                    continue

                # Dapatkan ukuran file dan timestamp saat ini
                size = os.path.getsize(fp)
                added_at = datetime.utcnow().isoformat()

                # Tambahkan track ke database
                cur.execute("""
                    INSERT INTO mp3_tracks
                    (folder_id, filename, filepath, size, added_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (folder_id, fn, fp, size, added_at, owner))

                tracks_added.append(fn)

        # Commit perubahan ke database
        conn.commit()

    except Exception as e:
        # Rollback jika terjadi error dan kembalikan pesan error
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        # Pastikan koneksi database ditutup
        conn.close()

    # Return hasil pemindaian dan impor
    return jsonify({
        "status": "ok",
        "folders_added": folders_added,
        "tracks_added": tracks_added,
        "message": f"{len(folders_added)} folder dan {len(tracks_added)} MP3 ditemukan."
    })