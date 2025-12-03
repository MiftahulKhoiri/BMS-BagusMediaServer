#!/usr/bin/env python3
# launcher.py - Entrypoint BMS Launcher modular

import os
import sys
from BMS_detect import detect, pretty_print

# Import core modules
from core.env_tools import project_root, venv_path, get_python_in_venv, create_venv, install_requirements
from core.system_tools import run
from core.server_dev import run_development
from core.server_prod import run_production
from core.nginx_tools import generate_nginx_config, reload_nginx
from core.supervisor_tools import setup_supervisor
from core.monitor_tools import monitoring
from core.update_tools import auto_update
from core.repair_tools import auto_repair

# ------------------------------------------------------------
# 0. Detect environment
# ------------------------------------------------------------
env = detect()

print("=== BMS Environment Info ===")
pretty_print(env)
print("")

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
PROJECT_DIR = project_root()
VENV_DIR = venv_path()
VENV_PY = get_python_in_venv(VENV_DIR)
PY_EXEC = sys.executable

print(f"[i] PROJECT_DIR : {PROJECT_DIR}")
print(f"[i] VENV_DIR    : {VENV_DIR}")
print(f"[i] VENV_PY     : {VENV_PY}")
print("")

# ------------------------------------------------------------
# Ensure venv exists
# ------------------------------------------------------------
if not os.path.exists(VENV_DIR):
    create_venv(PY_EXEC)
else:
    print("[✓] venv ditemukan.")

# Install requirements (safe)
install_requirements(VENV_PY)
print("")

# ------------------------------------------------------------
# Menu
# ------------------------------------------------------------
def show_menu():
    print("Pilih Mode:")
    print("1) Development")
    print("2) Production")
    print("3) Info Environment")
    print("4) Setup Supervisor (Linux)")
    print("5) Exit")
    print("6) Monitoring System")
    print("7) Update System")
    print("8) Auto Repair System")
    print("")

    pilih = input("Pilihan [1-8]: ").strip()

    if pilih == "1":
        run_development(env, VENV_PY)

    elif pilih == "2":
        run_production(env, VENV_PY, PROJECT_DIR)

    elif pilih == "3":
        pretty_print(env)

    elif pilih == "4":
        setup_supervisor(env, PROJECT_DIR, VENV_PY)

    elif pilih == "5":
        print("Keluar...")
        sys.exit(0)

    elif pilih == "6":
        monitoring(env)

    elif pilih == "7":
        auto_update(env, PROJECT_DIR)

    elif pilih == "8":
        auto_repair(env, PROJECT_DIR)

    else:
        print("Pilihan tidak valid.")

if __name__ == "__main__":
    show_menu()