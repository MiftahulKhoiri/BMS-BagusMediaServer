# ============================================================================
#   BMS MP3 THUMBNAIL ROUTE — FINAL FIX
#   ✔ Thumbnail GLOBAL berbasis filepath
#   ✔ Auto decode URL path (FIX UTAMA)
#   ✔ Cache thumbnail
#   ✔ Auto extract ID3 cover
#   ✔ Fallback default image
# ============================================================================

import os
import hashlib
from urllib.parse import unquote

from flask import Blueprint, send_file, abort
from app.BMS_config import PICTURES_FOLDER
from app.routes.BMS_mp3.BMS_mp3_cover import extract_cover

# ============================================================================
#   BLUEPRINT
# ============================================================================
mp3_thumb = Blueprint("mp3_thumb", __name__, url_prefix="/mp3")

# ============================================================================
#   THUMBNAIL FOLDER
# ============================================================================
THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")
os.makedirs(THUMBNAIL_MP3_FOLDER, exist_ok=True)

# ============================================================================
#   HELPER: HASH BASED ON ABS PATH (GLOBAL)
# ============================================================================
def get_thumb_name(mp3_path: str) -> str:
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode("utf-8")).hexdigest() + ".jpg"

# ============================================================================
#   ROUTE: SERVE MP3 THUMBNAIL
# ============================================================================
@mp3_thumb.route("/thumbnail/<path:mp3_path>")
def serve_mp3_thumbnail(mp3_path):
    """
    mp3_path = path asli MP3 (URL encoded dari frontend)
    Alur:
    1. Decode URL
    2. Cek file MP3
    3. Kirim thumbnail cache jika ada
    4. Extract cover ID3 jika belum ada
    5. Fallback ke default image
    """

    # 🔥 FIX UTAMA: decode URL path
    mp3_path = unquote(mp3_path)
    mp3_path = os.path.abspath(mp3_path)

    # MP3 tidak ditemukan
    if not os.path.exists(mp3_path):
        abort(404)

    # Nama thumbnail global
    thumb_name = get_thumb_name(mp3_path)
    thumb_path = os.path.join(THUMBNAIL_MP3_FOLDER, thumb_name)

    # 1️⃣ Cache thumbnail
    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")

    # 2️⃣ Extract dari ID3
    try:
        ok = extract_cover(mp3_path, thumb_path)
        if ok and os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype="image/jpeg")
    except Exception:
        pass  # silent & aman

    # 3️⃣ Fallback default
    default_img = "static/img/mp3_default.jpg"
    if os.path.exists(default_img):
        return send_file(default_img, mimetype="image/jpeg")

    abort(404)