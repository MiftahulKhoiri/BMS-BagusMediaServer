# ============================================================================
#   BMS MP3 MODULE — THUMBNAIL ROUTE (FINAL)
#   ✔ Thumbnail MP3 berbasis PATH (GLOBAL)
#   ✔ Auto-extract ID3 saat diminta (1x cache)
#   ✔ URL decode aman (%2Fstorage%2F...)
#   ✔ Fallback default icon
# ============================================================================

import os
import hashlib
from urllib.parse import unquote
from flask import Blueprint, send_file, abort

from app.BMS_config import PICTURES_FOLDER
from app.routes.BMS_mp3.BMS_mp3_cover import extract_cover

mp3_thumb = Blueprint("mp3_thumb", __name__, url_prefix="/mp3")

# Folder cache thumbnail MP3
THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")
os.makedirs(THUMBNAIL_MP3_FOLDER, exist_ok=True)


def get_thumb_name(mp3_path: str) -> str:
    """
    Nama thumbnail konsisten berbasis PATH absolut
    """
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


@mp3_thumb.route("/thumbnail/<path:mp3_path>")
def serve_mp3_thumbnail(mp3_path):
    """
    mp3_path = path asli MP3 (URL encoded)
    Alur:
      1) decode URL path
      2) cek file MP3 ada
      3) jika thumbnail ada → kirim
      4) jika belum → extract ID3 → simpan → kirim
      5) gagal → default icon
    """
    # 🔥 PENTING: decode URL (%2Fstorage%2F...)
    mp3_path = unquote(mp3_path)
    mp3_path = os.path.abspath(mp3_path)

    # validasi file mp3
    if not os.path.exists(mp3_path):
        abort(404)

    thumb_name = get_thumb_name(mp3_path)
    thumb_path = os.path.join(THUMBNAIL_MP3_FOLDER, thumb_name)

    # 1️⃣ cache sudah ada
    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")

    # 2️⃣ belum ada → coba extract dari ID3
    try:
        ok = extract_cover(mp3_path, thumb_path)
        if ok and os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype="image/jpeg")
    except Exception:
        pass  # silent, lanjut fallback

    # 3️⃣ fallback default icon
    default_icon = os.path.join("static", "img", "mp3_default.jpg")
    if os.path.exists(default_icon):
        return send_file(default_icon, mimetype="image/jpeg")

    abort(404)