# ============================================================================
#   BMS MP3 MODULE — THUMBNAIL + COLOR ROUTE (FINAL COMPLETE)
#   ✔ Cache lokal
#   ✔ Extract ID3
#   ✔ Fetch MusicBrainz (1x)
#   ✔ Extract & cache dominant color
#   ✔ SELALU return image
# ============================================================================

import os
import hashlib
from urllib.parse import unquote
from flask import Blueprint, send_file, jsonify

from app.BMS_config import PICTURES_FOLDER
from app.routes.BMS_mp3.BMS_mp3_cover import extract_cover
from app.routes.BMS_mp3.BMS_mp3_online_cover import (
    search_musicbrainz_cover,
    download_image
)
from app.routes.BMS_mp3.BMS_mp3_dominant_color import extract_dominant_color

mp3_thumb = Blueprint("mp3_thumb", __name__, url_prefix="/mp3")

# ======================================================
# PATH
# ======================================================
THUMBNAIL_MP3_FOLDER = os.path.join(PICTURES_FOLDER, "thumbnail_mp3")
os.makedirs(THUMBNAIL_MP3_FOLDER, exist_ok=True)

DEFAULT_COVER = "static/img/mp3_default.jpg"
DEFAULT_COLOR = "#1b6cff"


# ======================================================
# HELPERS
# ======================================================
def get_thumb_name(mp3_path: str) -> str:
    key = os.path.abspath(mp3_path)
    return hashlib.md5(key.encode()).hexdigest() + ".jpg"


def save_dominant_color(thumb_path: str):
    """
    Extract & simpan warna dominan (1x)
    """
    try:
        color = extract_dominant_color(thumb_path)
        if not color:
            return
        with open(thumb_path + ".color", "w") as f:
            f.write(color)
    except Exception:
        pass


def normalize_mp3_path(mp3_path: str) -> str:
    mp3_path = unquote(mp3_path)
    if not mp3_path.startswith("/"):
        mp3_path = "/" + mp3_path
    return os.path.abspath(mp3_path)


# ======================================================
# THUMBNAIL ROUTE
# ======================================================
@mp3_thumb.route("/thumbnail/<path:mp3_path>")
def serve_mp3_thumbnail(mp3_path):
    mp3_path = normalize_mp3_path(mp3_path)

    # 🚨 Jangan pernah 404
    if not os.path.exists(mp3_path):
        return send_file(DEFAULT_COVER, mimetype="image/jpeg")

    thumb_name = get_thumb_name(mp3_path)
    thumb_path = os.path.join(THUMBNAIL_MP3_FOLDER, thumb_name)

    # 1️⃣ CACHE LOKAL
    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype="image/jpeg")

    # 2️⃣ EXTRACT ID3
    try:
        ok = extract_cover(mp3_path, thumb_path)
        if ok and os.path.exists(thumb_path):
            save_dominant_color(thumb_path)
            return send_file(thumb_path, mimetype="image/jpeg")
    except Exception:
        pass

    # 3️⃣ MUSICBRAINZ (ONLINE, 1x)
    try:
        cover_url = search_musicbrainz_cover(os.path.basename(mp3_path))
        if cover_url:
            ok = download_image(cover_url, thumb_path)
            if ok and os.path.exists(thumb_path):
                save_dominant_color(thumb_path)
                return send_file(thumb_path, mimetype="image/jpeg")
    except Exception:
        pass

    # 4️⃣ DEFAULT
    return send_file(DEFAULT_COVER, mimetype="image/jpeg")


# ======================================================
# DOMINANT COLOR ROUTE
# ======================================================
@mp3_thumb.route("/color/<path:mp3_path>")
def serve_mp3_color(mp3_path):
    mp3_path = normalize_mp3_path(mp3_path)

    if not os.path.exists(mp3_path):
        return jsonify({"color": DEFAULT_COLOR})

    thumb_name = get_thumb_name(mp3_path)
    color_file = os.path.join(
        THUMBNAIL_MP3_FOLDER,
        thumb_name + ".color"
    )

    if os.path.exists(color_file):
        try:
            with open(color_file) as f:
                return jsonify({"color": f.read().strip()})
        except Exception:
            pass

    return jsonify({"color": DEFAULT_COLOR})