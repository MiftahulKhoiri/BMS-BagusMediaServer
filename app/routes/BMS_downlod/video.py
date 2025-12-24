from yt_dlp import YoutubeDL
from app.routes.BMS_downlod.progress import yt_progress_hook
from app.BMS_config import BASE_DOWNLOADS_FOLDER

def unduh_video(url, resolusi=720):
    cek_ffmpeg()
    if not konfirmasi_mode_pribadi():
        return None

    # 📁 pastikan folder video ada
    video_folder = os.path.join(BASE_DOWNLOADS_FOLDER, "video")
    os.makedirs(video_folder, exist_ok=True)

    title, video = download_video(url, resolusi)
    audio = download_audio(url)

    nama = bersihkan_nama_file(title)
    output = os.path.join(video_folder, f"{nama}.mp4")

    merge_video_audio(video, audio, output)
    hapus_jika_ada(video, audio)

    return output