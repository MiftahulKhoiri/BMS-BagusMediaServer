import os
import re

ILLEGAL_CHARS = r'[<>:"/\\|?*]'

def bersihkan_nama_file(nama: str) -> str:
    nama = re.sub(ILLEGAL_CHARS, "", nama)
    return nama.strip()

def hapus_jika_ada(*files):
    for f in files:
        if f and os.path.exists(f):
            os.remove(f)

def buat_nama_unik(folder, nama, ext):
    base = nama
    i = 1
    hasil = f"{base}.{ext}"

    while os.path.exists(os.path.join(folder, hasil)):
        hasil = f"{base}_{i}.{ext}"
        i += 1

    return hasil