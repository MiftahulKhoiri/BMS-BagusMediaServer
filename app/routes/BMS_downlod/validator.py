import shutil

def cek_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg tidak ditemukan")

def konfirmasi_mode_pribadi():
    print("⚠️ Hanya untuk konten milik sendiri / Creative Commons")
    jawab = input("Lanjutkan? (y/n): ")
    return jawab.lower() == "y"