import os
from app.BMS_config import BASE, MUSIC_FOLDER, VIDEO_FOLDER

# =====================================================
# ROOT PROJECT
# =====================================================
ROOT = os.path.realpath(BASE)

# =====================================================
# TEMP UPLOAD (CHUNK)
# =====================================================
UPLOAD_INTERNAL = os.path.join(ROOT, ".uploads")
BACKUP_INTERNAL = os.path.join(ROOT, ".backups")

os.makedirs(UPLOAD_INTERNAL, exist_ok=True)
os.makedirs(BACKUP_INTERNAL, exist_ok=True)

# pastikan folder media ada
os.makedirs(MUSIC_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# =====================================================
# DETEKSI FOLDER TUJUAN BERDASARKAN FILE
# =====================================================
def detect_target_folder(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]

    # AUDIO
    if ext in [".mp3", ".wav", ".flac", ".aac", ".ogg"]:
        return MUSIC_FOLDER

    # VIDEO
    if ext in [".mp4", ".mkv", ".avi", ".mov", ".webm"]:
        return VIDEO_FOLDER

    # DEFAULT (jika mau)
    return ROOT


# =====================================================
# PATH FINAL AMAN (ANTI TRAVERSAL)
# =====================================================
def internal_path(filename: str) -> str:
    """
    Tentukan path final file upload berdasarkan tipe file
    """
    target_dir = detect_target_folder(filename)

    base = os.path.join(target_dir, filename)
    real = os.path.realpath(base)

    if not real.startswith(os.path.realpath(target_dir)):
        raise RuntimeError("Blocked path traversal attempt")

    return real