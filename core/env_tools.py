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
    if venv_dir is None:
        venv_dir = venv_path()

    candidates = [
        os.path.join(venv_dir, "Scripts", "python.exe"),  # Windows
        os.path.join(venv_dir, "Scripts", "python"),       # Windows (non-.exe)
        os.path.join(venv_dir, "bin", "python3"),          # Linux / Raspberry Pi
        os.path.join(venv_dir, "bin", "python3.9"),        # Python 3.9 specific
        os.path.join(venv_dir, "bin", "python3.10"),       # Python 3.10 specific
        os.path.join(venv_dir, "bin", "python3.11"),       # Python 3.11 specific
        os.path.join(venv_dir, "bin", "python"),           # Termux / Mac OS lama
    ]

    for c in candidates:
        if os.path.exists(c):
            # Verifikasi bahwa ini benar-benar executable Python
            try:
                result = subprocess.run([c, "--version"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=2)
                if result.returncode == 0:
                    return c
            except:
                continue

    # Coba cari dengan which jika di PATH
    if os.name == "posix":
        python_in_venv = os.path.join(venv_dir, "bin", "python")
        if os.path.exists(python_in_venv):
            return python_in_venv
    
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