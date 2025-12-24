import os
import sys
import platform
import json

# ============================================================
#  BMS CONFIG — Versi Universal (Dirapikan)
#  Tetap 100% kompatibel Termux & Android
# ============================================================

VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")

# ============================================================
# 1. Load & Save Version
# ============================================================
def BMS_load_version():
    try:
        with open(VERSION_FILE, "r") as f:
            return json.load(f)
    except:
        return {"version": "1.0.0", "commit": "local"}


def BMS_save_version(version, commit):
    data = {"version": version, "commit": commit}
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
# 2. Deteksi TERMUX
# ============================================================
def is_termux():
    exe = sys.executable
    home = os.path.expanduser("~")

    return (
        exe.startswith("/data/data/com.termux/") or
        home.startswith("/data/data/com.termux/")
    )


# ============================================================
# 3. Deteksi BASE Folder
# ============================================================
def detect_bms_base():

    # 1. TERMUX
    if is_termux():
        return "/data/data/com.termux/files/home/storage/downloads/BMS"

    # 2. ANDROID (non-Termux)
    possible_android_paths = [
        "/storage/emulated/0/Download/BMS",
        "/sdcard/Download/BMS"
    ]
    for p in possible_android_paths:
        if os.path.exists(os.path.dirname(p)):
            return p

    # 3. WINDOWS
    if platform.system().lower() == "windows":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # 4. macOS
    if platform.system().lower() == "darwin":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # 5. LINUX SERVER
    project_base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return project_base


# ============================================================
# 4. BASE PATH AKHIR
# ============================================================
BASE = detect_bms_base()
print("[BMS CONFIG] BASE Detected:", BASE)


# ============================================================
# 5. DEFINISI FOLDER
# ============================================================
DB_FOLDER       = os.path.join(BASE, "database")
LOG_FOLDER      = os.path.join(BASE, "logs")
PICTURES_FOLDER  = os.path.join(BASE, "Pictures")
MUSIC_FOLDER    = os.path.join(BASE, "music")
VIDEO_FOLDER    = os.path.join(BASE, "video")
UPLOAD_FOLDER   = os.path.join(BASE, "upload")
DOWNLOADS_FOLDER   = os.path.join(BASE, "downloads")

DB_PATH = os.path.join(DB_FOLDER, "users.db")
LOG_PATH = os.path.join(LOG_FOLDER, "system.log")


# ============================================================
# 6. BUAT FOLDER OTOMATIS
# ============================================================
for folder in [
    BASE, DB_FOLDER, LOG_FOLDER,
    PICTURES_FOLDER, MUSIC_FOLDER,
    VIDEO_FOLDER, UPLOAD_FOLDER,
    DOWNLOADS_FOLDER
]:
    try:
        os.makedirs(folder, exist_ok=True)
    except:
        pass