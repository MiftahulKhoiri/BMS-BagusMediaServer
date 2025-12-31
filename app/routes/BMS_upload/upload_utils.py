import shutil
import os

def detect_category(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]

    if ext in [".mp3", ".wav", ".flac"]:
        return "media/mp3"
    if ext in [".mp4", ".mkv", ".avi"]:
        return "media/video"

    return "media/other"

def check_disk_space(required_size: int) -> bool:
    total, used, free = shutil.disk_usage("/")
    return free > required_size