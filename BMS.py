#!/usr/bin/env python3

"""
BMS Launcher (FINAL UNIVERSAL VERSION)
Aman untuk: Linux, Raspberry Pi OS Bookworm, Termux, Windows, macOS.
"""

import sys
from BMS_detect import detect, pretty_print

# Import core modules
from core.env_tools import (
    project_root, venv_path, create_venv,
    get_python_in_venv, install_requirements
)
from core.server_dev import run_development
from core.server_prod import run_production
from core.supervisor_tools import setup_supervisor
from core.monitor_tools import monitoring
from core.update_tools import auto_update
from core.repair_tools import auto_repair


# ------------------------------------------------------------
# 0. DETECT ENVIRONMENT
# ------------------------------------------------------------
env = detect()

print("=== BMS Environment Info ===")
pretty_print(env)
print("")


# ------------------------------------------------------------
# 1. PATH SETUP
# ------------------------------------------------------------
PROJECT_DIR = project_root()
VENV_DIR = venv_path()

print(f"[i] PROJECT_DIR : {PROJECT_DIR}")
print(f"[i] VENV_DIR    : {VENV_DIR}")
print("")


# ------------------------------------------------------------
# 2. SETUP VENV
# ------------------------------------------------------------
VENV_PY = get_python_in_venv(VENV_DIR)

if not VENV_PY:
    print("[!] venv tidak ditemukan, membuat baru...")
    create_venv(sys.executable)
    VENV_PY = get_python_in_venv(VENV_DIR)

print(f"[i] VENV_PY     : {VENV_PY}")
print("")


# ------------------------------------------------------------
# 3. INSTALL REQUIREMENTS (SELALU DI VENV)
# ------------------------------------------------------------
print("[+] Upgrade pip di venv...")
install_requirements(VENV_PY)

print("")
print("=== Environment siap ===")
print("")


# ------------------------------------------------------------
# 4. MENU UTAMA
# ------------------------------------------------------------

def show_menu():
    print("Pilih Mode:")
    print("1) Development")
    print("2) Production")
    print("3) Info Environment")
    print("4) Setup Supervisor (Linux)")
    print("5) Monitoring System")
    print("6) Update System")
    print("7) Auto Repair System")
    print("0) Exit")
    print("")

    pilih = input("Pilihan [1-7]: ").strip()

    if pilih == "1":
        run_development(env, VENV_PY)

    elif pilih == "2":
        run_production(env, VENV_PY, PROJECT_DIR)

    elif pilih == "3":
        pretty_print(env)

    elif pilih == "4":
        setup_supervisor(env, PROJECT_DIR, VENV_PY)

    elif pilih == "5":
        monitoring(env)

    elif pilih == "6":
        auto_update(env, PROJECT_DIR)

    elif pilih == "7":
        auto_repair(env, PROJECT_DIR)

    elif pilih == "0":
        print("Keluar...")
        sys.exit(0)

    else:
        print("[!] Pilihan tidak valid.")

# ------------------------------------------------------------
# 5. RUN MENU
# ------------------------------------------------------------
if __name__ == "__main__":
    while True:
        show_menu()

print("")
print("=== Launcher selesai ===")