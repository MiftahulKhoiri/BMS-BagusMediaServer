#!/usr/bin/env python3

"""
BMS Launcher — Tahap 2
Fokus: Deteksi OS + Setup Virtual Environment + Install Dependencies
"""

import os
import subprocess
import sys
from BMS_detect import detect, pretty_print

# ------------------------------------------------------------
# 0. LOAD ENVIRONMENT INFO
# ------------------------------------------------------------
env = detect()

print("=== BMS Environment Info ===")
pretty_print(env)
print("")


# ------------------------------------------------------------
# 1. PATH FOLDER PROJECT
# ------------------------------------------------------------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, "venv")
PYTHON_EXEC = sys.executable

print(f"[i] PROJECT_DIR : {PROJECT_DIR}")
print(f"[i] VENV_DIR    : {VENV_DIR}")
print("")


# ------------------------------------------------------------
# 2. FUNGSI SISTEM
# ------------------------------------------------------------
def run(cmd: str):
    """Jalankan command shell dengan print, aman untuk semua OS."""
    print(f"[cmd] {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("[!] Error menjalankan command!")
    return result.returncode


def create_venv():
    print("[+] Membuat Virtual Environment...")
    run(f"{PYTHON_EXEC} -m venv venv")


def install_requirements():
    req = os.path.join(PROJECT_DIR, "requirements.txt")

    # Tidak ada requirements.txt
    if not os.path.exists(req):
        print("[!] requirements.txt tidak ditemukan.")
        return

    print("[+] Upgrade pip...")
    run(f"{os.path.join(VENV_DIR, 'bin', 'python')} -m pip install --upgrade pip setuptools wheel")

    print("[+] Install dependencies...")
    run(f"{os.path.join(VENV_DIR, 'bin', 'python')} -m pip install -r requirements.txt")


# ------------------------------------------------------------
# 3. CEK & BUAT VENV
# ------------------------------------------------------------
if not os.path.exists(VENV_DIR):
    create_venv()
else:
    print("[✓] venv ditemukan.")

print("")


# ------------------------------------------------------------
# 4. INSTALL REQUIREMENTS
# ------------------------------------------------------------
install_requirements()

print("")
print("=== Tahap 2 selesai — Environment siap ===")
print("")


# ------------------------------------------------------------
# Launcher belum selesai — Mode server akan ditambahkan di Tahap 3
# ------------------------------------------------------------