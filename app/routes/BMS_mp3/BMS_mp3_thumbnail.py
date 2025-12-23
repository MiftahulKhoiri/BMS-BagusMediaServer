# ============================================================================
#   BMS MP3 MODULE — THUMBNAIL ROUTE (FINAL & SAFE)
#   ✔ Thumbnail MP3 berbasis PATH (GLOBAL)
#   ✔ Auto-extract ID3 saat diminta (1x cache)
#   ✔ URL decode aman
#   ✔ SELALU return image (no 404)
# ============================================================================

import os
import hashlib
from urllib.parse import unquote
from flask import Blueprint, send_file

from app.BMS_config import PICTURES_FOLDER
from app.routes.BMS_mp3.BMS_mp3_cover import extract_cover

mp3_thumb = Blueprint("mp3_thumb", __name__, url_prefix="/mp3")

# Folder cache thumbnail MP3
THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")
os.makedirs(THUMBNAIL_MP3_FOLDER, exist_ok=True)

DEFAULT_COVER = "static/img/mp3_default.jpg"


def get_thumb_name(mp3_path: str) -> str:
    """
    Nama thumbnail konsisten berbasis PATH absolut
    """
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


@mp3_thumb.route("/thumbnail/<path:mp3_path>")
def serve_mp3_thumbnail(mp3_path):
    # decode URL (%2Fstorage%2F...)
    mp3_path = unquote(mp3_path)

    # pastikan path absolut
    if not mp3_path.startswith("/"):
        mp3_path = "/" + mp3_path

    mp3_path = os.path.abspath(mp3_path)

    # 🚨 JANGAN PERNAH 404 DI THUMBNAIL
    if not os.path.exists(mp3_path):
        return send_file(DEFAULT_COVER, mimetype="image/jpeg")

    thumb_name = get_thumb_name(mp3_path)
    thumb_path = os.path.join(THUMBNAIL_MP3_FOLDER, thumb_name)

    # 1️⃣ Cache sudah ada
    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")

    # 2️⃣ Coba extract ID3
    try:
        ok = extract_cover(mp3_path, thumb_path)
        if ok and os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype="image/jpeg")
    except Exception:
        pass

    # 3️⃣ Fallback default (WAJIB)
    return send_file(DEFAULT_COVER, mimetype="image/jpeg")