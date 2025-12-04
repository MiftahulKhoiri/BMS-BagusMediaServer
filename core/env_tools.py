# core/env_tools.py
import os
import sys
from core.system_tools import run

def project_root():
    # return root folder (dua level di atas file ini)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def venv_path():
    return os.path.join(project_root(), "venv")

def get_python_in_venv(venv_dir=None):
    if venv_dir is None:
        venv_dir = venv_path()

    candidates = [
        os.path.join(venv_dir, "Scripts", "python.exe"),  # Windows
        os.path.join(venv_dir, "bin", "python3"),         # Linux / Raspberry Pi
        os.path.join(venv_dir, "bin", "python"),          # Termux / Mac OS lama
    ]

    for c in candidates:
        if os.path.exists(c):
            return c

    # tidak ada venv
    return None

def create_venv(python_exec=None):
    if python_exec is None:
        python_exec = sys.executable
    print("[+] Membuat Virtual Environment...")
    run(f"{python_exec} -m venv venv")

def install_requirements(venv_python=None):
    proj = project_root()
    req = os.path.join(proj, "requirements.txt")
    if not os.path.exists(req):
        print("[!] requirements.txt tidak ditemukan.")
        return
    if venv_python is None:
        venv_python = get_python_in_venv()
    print("[+] Upgrade pip di venv...")
    run(f"{venv_python} -m pip install --upgrade pip setuptools wheel")
    print("[+] Install dependencies dari requirements.txt ...")
    run(f"{venv_python} -m pip install -r {req}")