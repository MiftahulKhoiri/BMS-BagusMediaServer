import os

# ======================================================
#  🔍 DETEKSI LOKASI BMS (ANDROID / PC)
# ======================================================

# Jika Android / Termux
if os.path.exists("/storage/downloads/"):
    BASE = "/storage/downloads/BMS"

# Jika Android versi lama (fallback)
#elif os.path.exists("/storage/emulated/0/"):
   # BASE = "/storage/emulated/0/BMS"

# Jika PC (Windows / Linux)
else:
    BASE = os.path.expanduser("~/BMS")


# ======================================================
#  📁 DEFINISI FOLDER UTAMA
# ======================================================
DB_FOLDER       = f"{BASE}/database"
LOG_FOLDER      = f"{BASE}/logs"
PROFILE_FOLDER  = f"{BASE}/profile"
MP3_FOLDER      = f"{BASE}/MP3"
VIDEO_FOLDER    = f"{BASE}/VIDEO"
UPLOAD_FOLDER   = f"{BASE}/UPLOAD"


# ======================================================
#  📦 DEFINISI FILE UTAMA
# ======================================================
DB_PATH  = f"{DB_FOLDER}/users.db"
LOG_PATH = f"{LOG_FOLDER}/system.log"


# ======================================================
#  📌 PASTIKAN SEMUA FOLDER TERBUAT
# ======================================================

REQUIRED_FOLDERS = [
    BASE,
    DB_FOLDER,
    LOG_FOLDER,
    PROFILE_FOLDER,
    MP3_FOLDER,
    VIDEO_FOLDER,
    UPLOAD_FOLDER,
]

for path in REQUIRED_FOLDERS:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Tidak bisa membuat folder: {path} -> {e}")