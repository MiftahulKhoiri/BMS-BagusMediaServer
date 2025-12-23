import os
import hashlib

def mp3_thumb_hash(mp3_path: str) -> str:
    """
    HASH GLOBAL MP3 THUMBNAIL
    WAJIB dipakai di scan & serve
    """
    path = os.path.realpath(mp3_path)
    path = os.path.normpath(path)
    return hashlib.md5(path.encode("utf-8")).hexdigest() + ".jpg"