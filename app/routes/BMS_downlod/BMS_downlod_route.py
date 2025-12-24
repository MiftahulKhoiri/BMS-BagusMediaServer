# ============================================================
# BMS_downlod_route.py
# Route internal downloader BMS (DEV / PRIBADI)
# ============================================================

from flask import Blueprint, request, jsonify

from app.routes.BMS_downlod.downloader import unduh_video
from app.routes.BMS_downlod.audio import download_mp3
from app.routes.BMS_downlod.file_helper import bersihkan_nama_file
from app.routes.BMS_downlod.utils_info import ambil_info_video
from app.routes.BMS_downlod.db import get_db
from app.routes.BMS_downlod.db import ambil_semua_download
from app.routes.BMS_downlod.progress_store import buat_task, get_task
from app.routes.BMS_downlod.maintenance import cleanup_file_lama
from app.routes.BMS_utils import require_root
from app.routes.BMS_downlod.maintenance import hapus_download_id

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
    """
    Body JSON:
    {
        "url": "https://youtube.com/...",
        "resolusi": 720
    }
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON tidak valid"}), 400

    url = data.get("url")
    resolusi = data.get("resolusi", 720)

    if not url:
        return jsonify({"error": "URL wajib diisi"}), 400

    try:
        hasil = unduh_video(url, resolusi)
        if not hasil:
            return jsonify({
                "status": "dibatalkan",
                "message": "Download dibatalkan oleh pengguna"
            }), 200

        return jsonify({
            "status": "sukses",
            "tipe": "video",
            "file": hasil
        })

    except Exception as e:
        return jsonify({
            "status": "gagal",
            "error": str(e)
        }), 500


# ============================================================
# ROUTE: DOWNLOAD AUDIO (MP3)
# ============================================================

@BMS_downlod_bp.route("/audio", methods=["POST"])
def download_audio_route():
    """
    Body JSON:
    {
        "url": "https://youtube.com/..."
    }
    """

    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return jsonify({"error": "URL wajib diisi"}), 400

    url = data["url"]

    try:
        # 🔎 ambil info video (judul asli)
        info = ambil_info_video(url)
        title = bersihkan_nama_file(info.get("title", "audio"))

        # 🎵 download mp3
        hasil = download_mp3(url, title)

        # 💾 simpan ke database
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
            "file": hasil
        })

    except Exception as e:
        return jsonify({
            "status": "gagal",
            "error": str(e)
        }), 500

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
            "total": len(data),
            "data": data
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500




@BMS_downlod_bp.route("/progress/<task_id>", methods=["GET"])
def cek_progress(task_id):
    data = get_task(task_id)
    if not data:
        return jsonify({"error": "task_id tidak ditemukan"}), 404
    return jsonify(data)


@BMS_downlod_bp.route("/cleanup", methods=["POST"])
def cleanup_download():
    cek = require_root()
    if cek:
        return cek

    hari = request.json.get("hari", 30)

    try:
        total = cleanup_file_lama(hari)
        return jsonify({
            "status": "sukses",
            "dihapus": total,
            "hari": hari
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500


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
            "id": download_id
        })
    except Exception as e:
        return jsonify({"status": "gagal", "error": str(e)}), 500