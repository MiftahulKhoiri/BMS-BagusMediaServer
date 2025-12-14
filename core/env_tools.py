# core/env_tools.py
import os
import sys
from core.system_tools import run

def project_root():
    """
    Mengembalikan path absolut dari root folder proyek.
    Root folder adalah dua level di atas file ini.
    
    Returns:
        str: Path absolut ke root folder proyek.
    """
    # return root folder (dua level di atas file ini)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def venv_path():
    """
    Mengembalikan path lengkap ke folder virtual environment.
    Diasumsikan virtual environment berada di folder 'venv' di root proyek.
    
    Returns:
        str: Path lengkap ke folder virtual environment.
    """
    return os.path.join(project_root(), "venv")

def get_python_in_venv(venv_dir=None):
    """
    Mencari executable Python di dalam virtual environment.
    Fungsi ini mendeteksi berbagai platform (Windows, Linux, Raspberry Pi, Termux, dll).
    
    Args:
        venv_dir (str, optional): Path ke folder virtual environment. 
                                 Jika None, akan menggunakan venv_path().
    
    Returns:
        str or None: Path ke executable Python dalam venv, atau None jika tidak ditemukan.
    """
    if venv_dir is None:
        venv_dir = venv_path()

    # Daftar kemungkinan lokasi executable Python di berbagai platform
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
    """
    Membuat virtual environment baru menggunakan venv module.
    
    Args:
        python_exec (str, optional): Path ke executable Python yang akan digunakan.
                                    Jika None, akan menggunakan sys.executable (Python yang sedang berjalan).
    """
    if python_exec is None:
        python_exec = sys.executable
    print("[+] Membuat Virtual Environment...")
    run(f"{python_exec} -m venv venv")

def install_requirements(venv_python=None):
    """
    Menginstall dependencies dari requirements.txt menggunakan pip di virtual environment.
    
    Args:
        venv_python (str, optional): Path ke executable Python dalam virtual environment.
                                    Jika None, akan menggunakan get_python_in_venv() untuk mencarinya.
    """
    proj = project_root()
    req = os.path.join(proj, "requirements.txt")
    
    # Cek apakah file requirements.txt ada
    if not os.path.exists(req):
        print("[!] requirements.txt tidak ditemukan.")
        return
    
    # Gunakan executable Python dari venv jika tidak disediakan
    if venv_python is None:
        venv_python = get_python_in_venv()
    
    # Upgrade pip dan tools instalasi
    print("[+] Upgrade pip di venv...")
    run(f"{venv_python} -m pip install --upgrade pip setuptools wheel")
    
    # Install dependencies dari requirements.txt
    print("[+] Install dependencies dari requirements.txt ...")
    run(f"{venv_python} -m pip install -r {req}")