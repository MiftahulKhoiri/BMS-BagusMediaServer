import os
import hashlib
from flask import Blueprint, send_file, abort
from app.BMS_config import PICTURES_FOLDER

mp3_thumb = Blueprint("mp3_thumb", __name__, url_prefix="/mp3")

THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")


def get_thumb_name(mp3_path):
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


@mp3_thumb.route("/thumbnail/<path:mp3_path>")
def serve_mp3_thumbnail(mp3_path):
    """
    mp3_path = path asli mp3 (URL encoded)
    """
    thumb = get_thumb_name(mp3_path)
    thumb_path = os.path.join(THUMBNAIL_MP3_FOLDER, thumb)

    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")

    # fallback default icon
    default = "static/img/mp3_default.jpg"
    if os.path.exists(default):
        return send_file(default, mimetype="image/jpeg")

    abort(404)