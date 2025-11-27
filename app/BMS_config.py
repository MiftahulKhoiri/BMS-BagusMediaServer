import os
import platform


# =====================================================
# 🔥 FUNGSI DETEKSI SISTEM & FOLDER BMS
# =====================================================
def detect_bms_base():
    system = platform.system().lower()

    # -------------------------------------------------
    # 1️⃣ DETEKSI TERMUX
    # -------------------------------------------------
    termux_storage = "/data/data/com.termux/files/home/storage"

    if os.path.exists(f"{termux_storage}/downloads"):
        return f"{termux_storage}/downloads/BMS"

    # -------------------------------------------------
    # 2️⃣ DETEKSI ANDROID NORMAL
    # -------------------------------------------------
    # Android Download folder (versi baru)
    if os.path.exists("/storage/emulated/0/Download"):
        return "/storage/emulated/0/Download/BMS"

    # Android versi lama
    if os.path.exists("/sdcard/Download"):
        return "/sdcard/Download/BMS"

    # -------------------------------------------------
    # 3️⃣ DETEKSI WINDOWS
    # -------------------------------------------------
    if "windows" in system:
        return os.path.expanduser("~/BMS")

    # -------------------------------------------------
    # 4️⃣ DETEKSI LINUX (PC)
    # -------------------------------------------------
    if "linux" in system:
        return os.path.expanduser("~/BMS")

    # -------------------------------------------------
    # 5️⃣ DETEKSI MAC
    # -------------------------------------------------
    if "darwin" in system:
        return os.path.expanduser("~/BMS")

    # -------------------------------------------------
    # Default fallback
    # -------------------------------------------------
    return os.path.expanduser("~/BMS")


# =====================================================
# 📌 JALANKAN DETEKSI
# =====================================================
BASE = detect_bms_base()


# =====================================================
# 📁 DEFINISI FOLDER UTAMA
# =====================================================
DB_FOLDER       = f"{BASE}/database"
LOG_FOLDER      = f"{BASE}/logs"
PROFILE_FOLDER  = f"{BASE}/profile"
MP3_FOLDER      = f"{BASE}/MP3"
VIDEO_FOLDER    = f"{BASE}/VIDEO"
UPLOAD_FOLDER   = f"{BASE}/UPLOAD"


# =====================================================
# 📦 FILE UTAMA
# =====================================================
DB_PATH  = f"{DB_FOLDER}/users.db"
LOG_PATH = f"{LOG_FOLDER}/system.log"


# =====================================================
# 📌 PASTIKAN SEMUA FOLDER TERBUAT
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

for path in REQUIRED_FOLDERS:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Gagal membuat folder: {path} -> {e}")


# INFO DEBUG (opsional)
print("[BMS] BASE:", BASE)
print("[BMS] DB_PATH:", DB_PATH)
print("[BMS] LOG_PATH:", LOG_PATH)