import os
from app.BMS_config import BASE_DOWNLOADS_FOLDER
from app.routes.BMS_downlod.video import download_video
from app.routes.BMS_downlod.audio import download_audio
from app.routes.BMS_downlod.ffmpeg_merge import merge_video_audio
from app.routes.BMS_downlod.file_helper import (
    bersihkan_nama_file,
    hapus_jika_ada,
    buat_nama_unik
)
from app.routes.BMS_downlod.validator import cek_ffmpeg, konfirmasi_mode_pribadi
from app.routes.BMS_downlod.utils_info import ambil_info_video
from app.routes.BMS_downlod.db import get_db

def unduh_video(url, resolusi=720):
    cek_ffmpeg()
    if not konfirmasi_mode_pribadi():
        return None

    video_folder = os.path.join(BASE_DOWNLOADS_FOLDER, "video")
    os.makedirs(video_folder, exist_ok=True)

    info = ambil_info_video(url)
    title = bersihkan_nama_file(info["title"])

    title_video, video = download_video(url, resolusi)
    audio = download_audio(url)

    nama_file = buat_nama_unik(video_folder, title, "mp4")
    output = os.path.join(video_folder, nama_file)

    merge_video_audio(video, audio, output)
    hapus_jika_ada(video, audio)

    # simpan ke DB
    db = get_db()
    db.execute(
        "INSERT INTO downloads (tipe, title, file_path, source_url) VALUES (?,?,?,?)",
        ("video", title, output, url)
    )
    db.commit()
    db.close()

    return output