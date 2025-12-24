from yt_dlp import YoutubeDL
from app.routes.BMS_downlod.progress import yt_progress_hook
from app.BMS_config import BASE_DOWNLOADS_FOLDER
import os

def download_mp3(url, nama_file):
    # 📁 pastikan folder mp3 ada
    mp3_folder = os.path.join(BASE_DOWNLOADS_FOLDER, "mp3")
    os.makedirs(mp3_folder, exist_ok=True)

    opsi = {
        "format": "bestaudio",
        "outtmpl": os.path.join(mp3_folder, f"{nama_file}.%(ext)s"),
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