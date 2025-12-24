from yt_dlp import YoutubeDL
from app.routes.BMS_downlod.progress import yt_progress_hook

def download_audio(url):
    opsi = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": "temp_audio.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "progress_hooks": [yt_progress_hook],
    }

    with YoutubeDL(opsi) as ydl:
        info = ydl.extract_info(url, download=True)
        return f"temp_audio.{info.get('ext','m4a')}"