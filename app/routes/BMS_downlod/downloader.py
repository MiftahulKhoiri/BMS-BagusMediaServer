# ============================================================
# downloader.py
# Handle VIDEO download (MP4) saja
# ============================================================

import os

from app.BMS_config import DOWNLOADS_FOLDER
from app.routes.BMS_downlod.video import download_video
from app.routes.BMS_downlod.ffmpeg_merge import merge_video_audio
from app.routes.BMS_downlod.file_helper import (
    bersihkan_nama_file,
    buat_nama_unik,
    hapus_jika_ada
)
from app.routes.BMS_downlod.utils_info import ambil_info_video
from app.routes.BMS_downlod.db import get_db
from app.routes.BMS_downlod.validator import cek_ffmpeg

def unduh_video(url, resolusi=720, task_id=None):
    """
    Download VIDEO (MP4) + AUDIO lalu merge
    """

    cek_ffmpeg()

    # 📁 folder video
    video_folder = os.path.join(DOWNLOADS_FOLDER, "video")
    os.makedirs(video_folder, exist_ok=True)

    # 🔎 info video
    info = ambil_info_video(url)
    title = bersihkan_nama_file(info.get("title", "video"))

    # ⬇️ download video
    _, temp_video = download_video(url, resolusi, task_id=task_id)

    # ⬇️ download audio (LAZY IMPORT, NO CIRCULAR)
    from app.routes.BMS_downlod.audio_video_helper import download_audio_for_video
    temp_audio = download_audio_for_video(url, task_id=task_id)

    # 🧹 nama output
    nama_file = buat_nama_unik(video_folder, title, "mp4")
    output = os.path.join(video_folder, nama_file)

    # 🔀 merge
    merge_video_audio(temp_video, temp_audio, output)

    # 🧹 cleanup temp
    hapus_jika_ada(temp_video, temp_audio)

    # 💾 simpan DB
    db = get_db()
    db.execute(
        "INSERT INTO downloads (tipe, title, file_path, source_url) VALUES (?,?,?,?)",
        ("video", title, output, url)
    )
    db.commit()
    db.close()

    return output