import shutil
import hashlib

def check_disk_space(root, required):
    stat = shutil.disk_usage(root)
    return stat.free > (required * 2)


CATEGORIES = {
    "music": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "video": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "docs":  [".pdf", ".txt", ".docx", ".xlsx", ".csv"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
}


def verify_md5(path, expected):
    if not expected:
        return True

    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    return h.hexdigest() == expected