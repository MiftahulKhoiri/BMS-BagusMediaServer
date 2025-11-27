import os
import platform

# =====================================================
# 🔥 DETEKSI LOKASI BMS (PRIORITAS TERMUX)
# =====================================================
def detect_bms_base():
    system = platform.system().lower()

    # -------------------------------------------------
    # 1️⃣ DETEKSI TERMUX (PRIORITAS MUTLAK)
    # -------------------------------------------------
    termux_storage = "/data/data/com.termux/files/home/storage"
    termux_download = os.path.join(termux_storage, "downloads")

    if os.path.exists(termux_download):
        # JIKA TERMUX TERDETEKSI → HENTIKAN DISINI
        return os.path.join(termux_download, "BMS")

    # -------------------------------------------------
    # 2️⃣ ANDROID BIASA (HANYA jika BUKAN Termux)
    # -------------------------------------------------
    android_download = "/storage/emulated/0/Download"
    android_download2 = "/sdcard/Download"

    if os.path.exists(android_download):
        return os.path.join(android_download, "BMS")

    if os.path.exists(android_download2):
        return os.path.join(android_download2, "BMS")

    # -------------------------------------------------
    # 3️⃣ WINDOWS
    # -------------------------------------------------
    if "windows" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------
    # 4️⃣ LINUX PC
    # -------------------------------------------------
    if "linux" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------
    # 5️⃣ MAC
    # -------------------------------------------------
    if "darwin" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------
    # Default
    # -------------------------------------------------
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
# 📌 BUAT SEMUA FOLDER
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