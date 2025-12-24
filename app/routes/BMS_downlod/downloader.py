import os
from app.routes.BMS_downlod.video import download_video
from app.routes.BMS_downlod.audio import download_audio
from app.routes.BMS_downlod.ffmpeg_merge import merge_video_audio
from app.routes.BMS_downlod.file_helper import (
    bersihkan_nama_file,
    hapus_jika_ada
)
from app.routes.BMS_downlod.validator import (
    cek_ffmpeg,
    konfirmasi_mode_pribadi
)

OUTPUT_DIR = "hasil_download"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def unduh_video(url, resolusi=720):
    cek_ffmpeg()
    if not konfirmasi_mode_pribadi():
        return None

    title, video = download_video(url, resolusi)
    audio = download_audio(url)

    nama = bersihkan_nama_file(title)
    output = os.path.join(OUTPUT_DIR, f"{nama}.mp4")

    merge_video_audio(video, audio, output)
    hapus_jika_ada(video, audio)

    return output