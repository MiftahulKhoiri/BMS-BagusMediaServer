from yt_dlp import YoutubeDL
from app.routes.BMS_downlod.progress import yt_progress_hook

def download_video(url, resolusi):
    opsi = {
        "format": f"bestvideo[height<={resolusi}][ext=mp4]/bestvideo",
        "outtmpl": "temp_video.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "progress_hooks": [yt_progress_hook],
    }

    with YoutubeDL(opsi) as ydl:
        info = ydl.extract_info(url, download=True)
        return info["title"], f"temp_video.{info.get('ext','mp4')}"