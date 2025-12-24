from yt_dlp import YoutubeDL
from app.routes.BMS_downlod.progress import yt_progress_hook
from app.BMS_config import BASE_DOWNLOADS_FOLDER
from app.routes.BMS_downlod.file_helper import buat_nama_unik
import os

def download_mp3(url, title):
    mp3_folder = os.path.join(BASE_DOWNLOADS_FOLDER, "mp3")
    os.makedirs(mp3_folder, exist_ok=True)

    nama_file = buat_nama_unik(mp3_folder, title, "mp3")

    opsi = {
        "format": "bestaudio",
        "outtmpl": os.path.join(mp3_folder, nama_file.replace(".mp3", ".%(ext)s")),
        "noplaylist": True,
        "quiet": True,
        "progress_hooks": [yt_progress_hook],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with YoutubeDL(opsi) as ydl:
        ydl.extract_info(url, download=True)

    return os.path.join(mp3_folder, nama_file)