# ============================================================
# BMS_downlod_route.py
# Route internal downloader BMS (DEV / PRIBADI)
# ============================================================

from flask import Blueprint, request, jsonify

from app.routes.BMS_downlod.downloader import unduh_video

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
# ROUTE: DOWNLOAD VIDEO
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
            "file": hasil
        })

    except Exception as e:
        return jsonify({
            "status": "gagal",
            "error": str(e)
        }), 500