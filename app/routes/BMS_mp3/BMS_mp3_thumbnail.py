import os
import hashlib
from flask import Blueprint, send_file, abort
from app.BMS_config import PICTURES_FOLDER
from app.routes.BMS_mp3.BMS_mp3_cover import extract_cover

mp3_thumb = Blueprint("mp3_thumb", __name__, url_prefix="/mp3")

THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")
os.makedirs(THUMBNAIL_MP3_FOLDER, exist_ok=True)


def get_thumb_name(mp3_path):
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


@mp3_thumb.route("/thumbnail/<path:mp3_path>")
def serve_mp3_thumbnail(mp3_path):
    """
    mp3_path = path asli mp3 (URL encoded)
    Thumbnail:
    - cache jika sudah ada
    - auto-extract dari ID3 jika belum
    """
    # pastikan path valid
    mp3_path = os.path.abspath(mp3_path)
    if not os.path.exists(mp3_path):
        abort(404)

    thumb_name = get_thumb_name(mp3_path)
    thumb_path = os.path.join(THUMBNAIL_MP3_FOLDER, thumb_name)

    # 1️⃣ jika thumbnail sudah ada → langsung kirim
    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")

    # 2️⃣ belum ada → coba extract dari ID3
    try:
        ok = extract_cover(mp3_path, thumb_path)
        if ok and os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype="image/jpeg")
    except Exception:
        pass  # silent & aman

    # 3️⃣ fallback default icon
    default = "static/img/mp3_default.jpg"
    if os.path.exists(default):
        return send_file(default, mimetype="image/jpeg")

    abort(404)