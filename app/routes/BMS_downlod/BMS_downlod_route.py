# ============================================================
# BMS_downlod_route.py
# Route internal downloader BMS (DEV / PRIBADI)
# ============================================================

from flask import Blueprint, request, jsonify

from app.routes.BMS_utils import require_root
from app.routes.BMS_downlod.downloader import unduh_video
from app.routes.BMS_downlod.file_helper import bersihkan_nama_file
from app.routes.BMS_downlod.utils_info import ambil_info_video

from app.routes.BMS_downlod.db import (
    get_db,
    ambil_semua_download
)

from app.routes.BMS_downlod.progress_store import (
    buat_task,
    get_task
)

from app.routes.BMS_downlod.maintenance import (
    cleanup_file_lama,
    hapus_download_id,
    sinkron_file_db
)

# ============================================================
# BLUEPRINT
# ============================================================

BMS_downlod_bp = Blueprint(
    "BMS_downlod",
    __name__,
    url_prefix="/bms/downlod"
)

# ============================================================
# ROUTE: TEST STATUS
# ============================================================

@BMS_downlod_bp.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "ok",
        "module": "BMS_downlod",
        "mode": "development"
    })

# ============================================================
# ROUTE: DOWNLOAD VIDEO (MP4)
# ============================================================

@BMS_downlod_bp.route("/video", methods=["POST"])
def download_video_route():
    data = request.get_json(silent=True) or {}

    url = data.get("url")
    resolusi = data.get("resolusi", 720)

    if not url:
        return jsonify({"error": "URL wajib diisi"}), 400

    task_id = buat_task()

    try:
        hasil = unduh_video(url, resolusi, task_id=task_id)
        if not hasil:
            return jsonify({
                "status": "dibatalkan",
                "task_id": task_id
            }), 200

        return jsonify({
            "status": "sukses",
            "tipe": "video",
            "task_id": task_id,
            "file": hasil
        })

    except Exception as e:
        return jsonify({
            "status": "gagal",
            "task_id": task_id,
            "error": str(e)
        }), 500

# ============================================================
# ROUTE: DOWNLOAD AUDIO (MP3)
# ============================================================

@BMS_downlod_bp.route("/audio", methods=["POST"])
def download_audio_route():
    # 🔥 LAZY IMPORT (memutus circular import)
    from app.routes.BMS_downlod.audio import download_mp3

    data = request.get_json(silent=True) or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL wajib diisi"}), 400

    task_id = buat_task()

    try:
        info = ambil_info_video(url)
        title = bersihkan_nama_file(info.get("title", "audio"))

        hasil = download_mp3(url, title, task_id=task_id)

        db = get_db()
        db.execute(
            """
            INSERT INTO downloads (tipe, title, file_path, source_url)
            VALUES (?,?,?,?)
            """,
            ("audio", title, hasil, url)
        )
        db.commit()
        db.close()

        return jsonify({
            "status": "sukses",
            "tipe": "audio",
            "task_id": task_id,
            "file": hasil
        })

    except Exception as e:
        return jsonify({
            "status": "gagal",
            "task_id": task_id,
            "error": str(e)
        }), 500

# ============================================================
# ROUTE: PROGRESS CHECK
# ============================================================

@BMS_downlod_bp.route("/progress/<task_id>", methods=["GET"])
def cek_progress(task_id):
    data = get_task(task_id)
    if not data:
        return jsonify({"error": "task_id tidak ditemukan"}), 404
    return jsonify(data)

# ============================================================
# ROUTE: DOWNLOAD HISTORY (ADMIN)
# ============================================================

@BMS_downlod_bp.route("/history", methods=["GET"])
def download_history():
    cek = require_root()
    if cek:
        return cek

    try:
        limit = request.args.get("limit", 50, type=int)
        data = ambil_semua_download(limit)
        return jsonify({
            "status": "sukses",
            "admin": True,
            "total": len(data),
            "data": data
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500

# ============================================================
# ROUTE: CLEANUP FILE LAMA (ADMIN)
# ============================================================

@BMS_downlod_bp.route("/cleanup", methods=["POST"])
def cleanup_download():
    cek = require_root()
    if cek:
        return cek

    data = request.get_json(silent=True) or {}
    hari = int(data.get("hari", 30))

    try:
        total = cleanup_file_lama(hari)
        return jsonify({
            "status": "sukses",
            "admin": True,
            "dihapus": total,
            "hari": hari
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500

# ============================================================
# ROUTE: DELETE DOWNLOAD BY ID (ADMIN)
# ============================================================

@BMS_downlod_bp.route("/delete/<int:download_id>", methods=["DELETE"])
def delete_download(download_id):
    cek = require_root()
    if cek:
        return cek

    try:
        ok = hapus_download_id(download_id)
        if not ok:
            return jsonify({"error": "Data tidak ditemukan"}), 404

        return jsonify({
            "status": "sukses",
            "admin": True,
            "id": download_id
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500

# ============================================================
# ROUTE: SYNC FILE <-> DATABASE (ADMIN)
# ============================================================

@BMS_downlod_bp.route("/sync", methods=["POST"])
def sync_downloads():
    cek = require_root()
    if cek:
        return cek

    try:
        total = sinkron_file_db()
        return jsonify({
            "status": "sukses",
            "admin": True,
            "db_dibersihkan": total
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500

@BMS_downlod_bp.route("/ui", methods=["GET"])
def ui_downlod():
   cek = BMS_profile_required()
    if cek:
        return cek
      render_template("BMS_downlod_user.html")
    
   return
render_template("BMS_downlod_admin.html")