import os
import platform

# =====================================================
# 🔥 DETEKSI LOKASI BMS (ANDROID / TERMUX / PC)
# =====================================================
def detect_bms_base():
    system = platform.system().lower()

    # 1️⃣ DETEKSI TERMUX
    termux_base = "/data/data/com.termux/files/home/storage"
    if os.path.exists(os.path.join(termux_base, "downloads")):
        return os.path.join(termux_base, "downloads", "BMS")

    # 2️⃣ ANDROID BIASA
    if os.path.exists("/storage/emulated/0/Download"):
        return "/storage/emulated/0/Download/BMS"

    if os.path.exists("/sdcard/Download"):
        return "/sdcard/Download/BMS"

    # 3️⃣ WINDOWS
    if "windows" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # 4️⃣ LINUX (PC)
    if "linux" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # 5️⃣ MAC
    if "darwin" in system:
        return os.path.join(os.path.expanduser("~"), "BMS")

    # Default fallback
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
# 📌 BUAT SEMUA FOLDER SECARA AUTOMATIS
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


# =====================================================
# 🧪 DEBUG INFO (opsional)
# =====================================================
print("folder selesai di buat")
