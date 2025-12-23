# ============================================================================
#   BMS MP3 — ONLINE COVER FETCH (MusicBrainz + Cover Art Archive)
#   ✔ Tanpa API Key
#   ✔ Gratis & legal
#   ✔ Cari cover 1x lalu cache
# ============================================================================

import re
import requests

HEADERS = {
    "User-Agent": "BMS-Media-Server/1.0 (contact: local-admin)"
}

# ============================================================
#   CLEAN TITLE
# ============================================================
def clean_title(filename: str) -> str:
    """
    Bersihkan nama file MP3 agar cocok untuk search
    """
    name = re.sub(r"\.mp3$", "", filename, flags=re.I)
    name = re.sub(r"\[.*?\]|\(.*?\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return name.strip()


# ============================================================
#   SEARCH MUSICBRAINZ
# ============================================================
def search_musicbrainz_cover(filename: str) -> str | None:
    """
    Cari cover dari MusicBrainz + Cover Art Archive
    Return: image_url atau None
    """
    title = clean_title(filename)
    if not title:
        return None

    try:
        r = requests.get(
            "https://musicbrainz.org/ws/2/recording/",
            params={
                "query": title,
                "fmt": "json",
                "limit": 1
            },
            headers=HEADERS,
            timeout=6
        )
        data = r.json()
    except Exception:
        return None

    recordings = data.get("recordings")
    if not recordings:
        return None

    releases = recordings[0].get("releases")
    if not releases:
        return None

    release_id = releases[0].get("id")
    if not release_id:
        return None

    # Cover Art Archive (front cover)
    return f"https://coverartarchive.org/release/{release_id}/front-500"


# ============================================================
#   DOWNLOAD IMAGE
# ============================================================
def download_image(url: str, dest: str) -> bool:
    """
    Download image ke file lokal
    """
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            with open(dest, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False