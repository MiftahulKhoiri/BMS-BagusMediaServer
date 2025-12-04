import os
import sys
import platform
import json

# ============================================================
#  BMS CONFIG — Versi Universal
#  Otomatis mendeteksi lokasi BASE di:
#  - Raspberry Pi / Linux Server
#  - Termux (HP Android)
#  - Android non-Termux
#  - Windows
#  - macOS
# ============================================================

VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")


# ============================================================
# 1. Fungsi Load & Save Versi Sistem
# ============================================================
def BMS_load_version():
    """Load versi dan commit dari version.json"""
    try:
        with open(VERSION_FILE, "r") as f:
            return json.load(f)
    except:
        return {"version": "1.0.0", "commit": "local"}


def BMS_save_version(version, commit):
    """Simpan versi ke version.json"""
    data = {"version": version, "commit": commit}
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
# 2. Deteksi Apakah Sedang Berjalan di Termux
# ============================================================
def is_termux():
    """
    Termux memiliki pola PATH Python yang unik.
    Jika Python berada di /data/data/com.termux → pasti Termux.
    """
    exe = sys.executable
    home = os.path.expanduser("~")

    if exe.startswith("/data/data/com.termux/"):
        return True

    if home.startswith("/data/data/com.termux/"):
        return True

    return False


# ============================================================
# 3. Deteksi BASE Path (SUPER AKURAT)
# ============================================================
def detect_bms_base():

    # -------------------------------------------------------
    # 🟢 1. TERMUX (Android Terminal)
    # -------------------------------------------------------
    if is_termux():
        return "/data/data/com.termux/files/home/storage/downloads/BMS"

    # -------------------------------------------------------
    # 🟡 2. ANDROID NON-TERMUX
    # -------------------------------------------------------
    if os.path.exists("/storage/emulated/0/Download"):
        return "/storage/emulated/0/Download/BMS"

    if os.path.exists("/sdcard/Download"):
        return "/sdcard/Download/BMS"

    # -------------------------------------------------------
    # 🔵 3. WINDOWS
    # -------------------------------------------------------
    if platform.system().lower() == "windows":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------------
    # 🟣 4. macOS
    # -------------------------------------------------------
    if platform.system().lower() == "darwin":
        return os.path.join(os.path.expanduser("~"), "BMS")

    # -------------------------------------------------------
    # 🔴 5. SERVER MODE (LINUX / RASPBERRY PI)
    # -------------------------------------------------------
    # Ini bagian PALING PENTING untuk server!
    # BASE otomatis diset ke folder project sebenarnya,
    # yaitu folder di mana file ini berada.
    PROJECT_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return PROJECT_BASE


# ============================================================
# 4. BASE PATH AKHIR
# ============================================================
BASE = detect_bms_base()

print("[BMS CONFIG] BASE Detected:", BASE)


# ============================================================
# 5. DEFINISI FOLDER SISTEM BMS
# ============================================================
DB_FOLDER       = os.path.join(BASE, "database")
LOG_FOLDER      = os.path.join(BASE, "logs")
PROFILE_FOLDER  = os.path.join(BASE, "profile")
MUSIC_FOLDER      = os.path.join(BASE, "music")
VIDEO_FOLDER    = os.path.join(BASE, "video")
UPLOAD_FOLDER   = os.path.join(BASE, "upload")

# File database utama
DB_PATH = os.path.join(DB_FOLDER, "users.db")

# File log sistem
LOG_PATH = os.path.join(LOG_FOLDER, "system.log")


# ============================================================
# 6. BUAT FOLDER-FOLDER JIKA BELUM ADA
# ============================================================
for folder in [
    BASE, DB_FOLDER, LOG_FOLDER,
    PROFILE_FOLDER, MP3_FOLDER,
    VIDEO_FOLDER, UPLOAD_FOLDER
]:
    try:
        os.makedirs(folder, exist_ok=True)
    except:
        pass