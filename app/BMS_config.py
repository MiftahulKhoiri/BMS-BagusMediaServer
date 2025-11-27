import os
import sys
import platform

# =====================================================
# 🔥  DETEKSI TERMUX SUPER AKURAT (berdasarkan Python PATH)
# =====================================================
def is_termux():
    exe = sys.executable
    home = os.path.expanduser("~")

    # Python Termux selalu ada dalam lokasi ini:
    if exe.startswith("/data/data/com.termux/"):
        return True

    # HOME Termux juga selalu seperti ini:
    if home.startswith("/data/data/com.termux/"):
        return True

    return False


# =====================================================
# 🔥  PILIH BASE PATH
# =====================================================
def detect_bms_base():

    # -------------------------------------------------
    # 🟢 1. JIKA TERMUX → PAKAI PATH INI & HENTI, SELESAI
    # -------------------------------------------------
    if is_termux():
        return "/data/data/com.termux/files/home/storage/downloads/BMS"

    # -------------------------------------------------
    # 🟡 2. ANDROID NON-TERMUX
    # -------------------------------------------------
    if os.path.exists("/storage/emulated/0/Download"):
        return "/storage/emulated/0/Download/BMS"

    if os.path.exists("/sdcard/Download"):
        return "/sdcard/Download/BMS"

    # -------------------------------------------------
    # 🔵 3. Windows
    # -------------------------------------------------
    if platform.system().lower() == "windows":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------
    # 🔴 4. Linux
    # -------------------------------------------------
    if platform.system().lower() == "linux":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------
    # 🟣 5. MacOS
    # -------------------------------------------------
    if platform.system().lower() == "darwin":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------
    # Default
    # -------------------------------------------------
    return os.path.join(os.path.expanduser("~"), "BMS")


# =====================================================
# 📌  HASIL DETEKSI BASE
# =====================================================
BASE = detect_bms_base()


# =====================================================
# 📁  DEFINISI FOLDER
# =====================================================
DB_FOLDER       = os.path.join(BASE, "database")
LOG_FOLDER      = os.path.join(BASE, "logs")
PROFILE_FOLDER  = os.path.join(BASE, "profile")
MP3_FOLDER      = os.path.join(BASE, "MP3")
VIDEO_FOLDER    = os.path.join(BASE, "VIDEO")
UPLOAD_FOLDER   = os.path.join(BASE, "UPLOAD")

DB_PATH = os.path.join(DB_FOLDER, "users.db")
LOG_PATH = os.path.join(LOG_FOLDER, "system.log")

# =====================================================
# 📌 BUAT FOLDER
# =====================================================
for folder in [
    BASE, DB_FOLDER, LOG_FOLDER,
    PROFILE_FOLDER, MP3_FOLDER,
    VIDEO_FOLDER, UPLOAD_FOLDER
]:
    try:
        os.makedirs(folder, exist_ok=True)
    except:
        pass

print("[BMS] BASE:", BASE)