from yt_dlp import YoutubeDL

def ambil_info_video(url):
    opsi = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True
    }
    with YoutubeDL(opsi) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "tanpa_judul"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url"),
        }