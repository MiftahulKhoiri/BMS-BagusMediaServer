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


# ============================================================
# 5. MODE SERVER (Tahap 3)
# ============================================================

def get_python_in_venv():
    """Mencari python di dalam venv otomatis untuk semua OS."""
    # Windows
    win_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    # Linux / Mac / Termux
    unix_path = os.path.join(VENV_DIR, "bin", "python")

    if os.path.exists(win_path):
        return win_path
    return unix_path


VENV_PY = get_python_in_venv()


# ------------------------------------------------------------
# MODE: DEVELOPMENT
# ------------------------------------------------------------
def run_development():
    print("=== MODE DEVELOPMENT ===")

    # Di Linux: gunakan gunicorn jika ada
    if env["os"] == "linux" and env["has_gunicorn"]:
        cmd = f"{VENV_PY} -m gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 BMS:create_app()"
        print("[i] Server Development: Gunicorn (Linux)")
    
    # Non-Linux pakai waitress
    else:
        cmd = f"{VENV_PY} -m waitress --listen=0.0.0.0:5000 BMS:create_app"
        print("[i] Server Development: Waitress (Cross-platform)")

    run(cmd)


# ------------------------------------------------------------
# MODE: PRODUCTION
# ------------------------------------------------------------
def run_production():
    print("=== MODE PRODUCTION ===")

    # Jika Linux, gunakan Gunicorn full power
    if env["os"] == "linux":
        cmd = (
            f"{VENV_PY} -m gunicorn -w 3 --threads 3 "
            f"-b 0.0.0.0:5000 BMS:create_app()"
        )
        print("[i] Production menggunakan Gunicorn (Linux)")

    else:
        # Selain Linux → fallback ke waitress
        cmd = f"{VENV_PY} -m waitress --listen=0.0.0.0:5000 BMS:create_app"
        print("[i] Production fallback (Waitress)")

    run(cmd)


# ------------------------------------------------------------
# 6. MENU MODE JALAN
# ------------------------------------------------------------

def show_menu():
    print("Pilih Mode:")
    print("1) Development")
    print("2) Production")
    print("3) Info Environment")
    print("4) Exit")
    print("")

    pilih = input("Pilihan [1-4]: ").strip()

    if pilih == "1":
        run_development()

    elif pilih == "2":
        run_production()

    elif pilih == "3":
        pretty_print(env)

    elif pilih == "4":
        print("Keluar...")
        sys.exit(0)

    else:
        print("Pilihan tidak valid.")


# ============================================================
# JALANKAN MENU
# ============================================================
show_menu()

print("")
print("=== Tahap 3 selesai — Server berjalan ===")