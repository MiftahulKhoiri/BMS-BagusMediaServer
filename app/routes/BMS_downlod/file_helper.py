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