# ============================================================
# BMS_downlod_route.py
# Route internal downloader BMS (DEV / PRIBADI)
# ============================================================

from flask import Blueprint, request, jsonify

from app.routes.BMS_downlod.downloader import unduh_video
from app.routes.BMS_downlod.audio import download_mp3
from app.routes.BMS_downlod.file_helper import bersihkan_nama_file

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
    if not data:
        return jsonify({"error": "Body JSON tidak valid"}), 400

    url = data.get("url")
    if not url:
        return jsonify({"error": "URL wajib diisi"}), 400

    try:
        # Ambil judul dulu (nama file aman)
        nama_file = bersihkan_nama_file("audio_youtube")

        download_mp3(url, nama_file)

        return jsonify({
            "status": "sukses",
            "tipe": "audio",
            "file": f"downloads/mp3/{nama_file}.mp3"
        })

    except Exception as e:
        return jsonify({
            "status": "gagal",
            "error": str(e)
        }), 500

from app.routes.BMS_downlod.utils_info import ambil_info_video
from app.routes.BMS_downlod.db import get_db

@BMS_downlod_bp.route("/audio", methods=["POST"])
def download_audio_route():
    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return jsonify({"error": "URL wajib diisi"}), 400

    url = data["url"]

    try:
        info = ambil_info_video(url)
        title = bersihkan_nama_file(info["title"])

        hasil = download_mp3(url, title)

        db = get_db()
        db.execute(
            "INSERT INTO downloads (tipe, title, file_path, source_url) VALUES (?,?,?,?)",
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
        return jsonify({"status": "gagal", "error": str(e)}), 500