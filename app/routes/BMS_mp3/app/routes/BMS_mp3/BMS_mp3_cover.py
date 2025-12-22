from mutagen.id3 import ID3, APIC

def extract_cover(mp3_path, save_path):
    """
    Ambil cover dari metadata MP3 (ID3 APIC).
    Return True jika berhasil, False jika tidak ada cover.
    """
    try:
        tags = ID3(mp3_path)
        for tag in tags.values():
            if isinstance(tag, APIC):
                with open(save_path, "wb") as img:
                    img.write(tag.data)
                return True
    except Exception:
        pass
    return False