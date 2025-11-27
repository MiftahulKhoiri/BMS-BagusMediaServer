import os
import platform

# =====================================================
# 🔥 DETEKSI LOKASI BMS (ANDROID / TERMUX / PC)
# =====================================================
def detect_bms_base():
    system = platform.system().lower()

    # TERMUX (prioritas utama)
    termux_storage = "/data/data/com.termux/files/home/storage"
    termux_download = os.path.join(termux_storage, "downloads")
    if os.path.exists(termux_download):
        return os.path.join(termux_download, "BMS")

    # ANDROID biasa
    if os.path.exists("/storage/emulated/0/Download"):
        return "/storage/emulated/0/Download/BMS"

    if os.path.exists("/sdcard/Download"):
        return "/sdcard/Download/BMS"

    # WINDOWS
    if "windows" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # LINUX
    if "linux" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # MAC
    if "darwin" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # Default
    return os.path.join(os.path.expanduser("~"), "BMS")


# =====================================================
# 📌 HASIL DETEKSI
# =====================================================
BASE = detect_bms_base()

# =====================================================
# 📁 DEFINISI FOLDER
# =====================================================
DB_FOLDER       = os.path.join(BASE, "database")
LOG_FOLDER      = os.path.join(BASE, "logs")
PROFILE_FOLDER  = os.path.join(BASE, "profile")
MP3_FOLDER      = os.path.join(BASE, "MP3")
VIDEO_FOLDER    = os.path.join(BASE, "VIDEO")
UPLOAD_FOLDER   = os.path.join(BASE, "UPLOAD")

# =====================================================
# 📦 FILE UTAMA
# =====================================================
DB_PATH  = os.path.join(DB_FOLDER, "users.db")
LOG_PATH = os.path.join(LOG_FOLDER, "system.log")

# =====================================================
# 📌 BUAT FOLDER
# =====================================================
REQUIRED_FOLDERS = [
    BASE,
    DB_FOLDER,
    LOG_FOLDER,
    PROFILE_FOLDER,
    MP3_FOLDER,
    VIDEO_FOLDER,
    UPLOAD_FOLDER,
]

for folder in REQUIRED_FOLDERS:
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Tidak bisa membuat folder '{folder}': {e}")

print("Folder selesai dibuat:", BASE)