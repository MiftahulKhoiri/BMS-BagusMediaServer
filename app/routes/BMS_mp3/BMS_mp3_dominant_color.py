# ============================================================================
#   BMS MP3 — DOMINANT COLOR EXTRACTOR
#   ✔ Ekstrak warna dominan dari cover (Pillow)
#   ✔ Aman & ringan
#   ✔ Cocok untuk UI theming
# ============================================================================

import os
from PIL import Image
from collections import Counter


def extract_dominant_color(image_path: str) -> str | None:
    """
    Mengambil warna dominan dari gambar
    Return: hex color (#rrggbb) atau None
    """
    if not os.path.exists(image_path):
        return None

    try:
        img = Image.open(image_path).convert("RGB")

        # kecilkan agar cepat
        img = img.resize((64, 64))

        pixels = list(img.getdata())

        # ambil warna paling sering
        most_common = Counter(pixels).most_common(1)
        if not most_common:
            return None

        r, g, b = most_common[0][0]
        return f"#{r:02x}{g:02x}{b:02x}"

    except Exception:
        return None