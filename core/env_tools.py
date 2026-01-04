# core/env_tools.py
import os
import sys
import subprocess
from pathlib import Path
from core.system_tools import run, is_command_available


def project_root() -> str:
    """
    Mengembalikan path absolut dari root folder proyek.
    Root folder adalah dua level di atas file ini.
    
    Returns:
        str: Path absolut ke root folder proyek.
    """
    # return root folder (tiga level di atas file ini untuk struktur: core/env_tools.py)
    current_dir = Path(__file__).parent
    return str(current_dir.parent.parent.absolute())


def venv_path() -> str:
    """
    Mengembalikan path lengkap ke folder virtual environment.
    Diasumsikan virtual environment berada di folder 'venv' di root proyek.
    
    Returns:
        str: Path lengkap ke folder virtual environment.
    """
    return os.path.join(project_root(), "venv")


def detect_python_executable() -> str:
    """
    Mendeteksi executable Python yang tersedia di sistem.
    Priority: python3 -> python -> sys.executable
    
    Returns:
        str: Path atau nama executable Python
    """
    # Daftar executable yang mungkin
    candidates = ["python3", "python3.11", "python3.10", "python3.9", "python"]
    
    for candidate in candidates:
        if is_command_available(candidate):
            try:
                # Verifikasi ini benar-benar Python
                result = subprocess.run(
                    [candidate, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0 and "Python" in result.stdout:
                    return candidate
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                continue
    
    # Fallback ke sys.executable
    return sys.executable


def get_python_in_venv(venv_dir: str = None) -> str:
    """
    Mendapatkan path ke executable Python di dalam virtual environment.
    
    Args:
        venv_dir (str): Path ke folder virtual environment
    
    Returns:
        str: Path ke executable Python, atau None jika tidak ditemukan
    """
    if venv_dir is None:
        venv_dir = venv_path()
    
    venv_dir = Path(venv_dir)
    
    # Daftar lokasi yang mungkin untuk executable Python
    candidates = []
    
    if sys.platform == "win32":
        # Windows
        candidates = [
            venv_dir / "Scripts" / "python.exe",
            venv_dir / "Scripts" / "pythonw.exe",
            venv_dir / "Scripts" / "python",
        ]
    else:
        # Unix-like (Linux, macOS, Termux)
        candidates = [
            venv_dir / "bin" / "python3",
            venv_dir / "bin" / "python3.11",
            venv_dir / "bin" / "python3.10",
            venv_dir / "bin" / "python3.9",
            venv_dir / "bin" / "python",
            venv_dir / "bin" / "python3.12",
            venv_dir / "bin" / "python3.8",
        ]
    
    # Untuk Termux khusus, cek juga di lokasi alternatif
    if os.path.exists("/data/data/com.termux/files/usr"):
        candidates.append(venv_dir / "bin" / "python3.11")
        candidates.append(venv_dir / "bin" / "python3.10")
        candidates.append(venv_dir / "bin" / "python")
    
    # Cek setiap kandidat
    for candidate in candidates:
        if candidate.exists():
            try:
                # Verifikasi executable
                result = subprocess.run(
                    [str(candidate), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and "Python" in result.stdout:
                    return str(candidate)
            except (subprocess.TimeoutExpired, PermissionError, OSError):
                continue
    
    # Jika tidak ditemukan, coba cari di sistem
    if sys.platform == "win32":
        # Cari python.exe di venv
        for root, dirs, files in os.walk(venv_dir):
            for file in files:
                if file.lower() in ["python.exe", "python3.exe"]:
                    candidate = Path(root) / file
                    if candidate.exists():
                        return str(candidate)
    else:
        # Cari dengan which jika PATH sudah di-setup
        venv_bin = venv_dir / "bin"
        if venv_bin.exists():
            for cmd in ["python3", "python"]:
                candidate = venv_bin / cmd
                if candidate.exists():
                    return str(candidate)
    
    return None


def is_venv_active() -> bool:
    """
    Mengecek apakah virtual environment sedang aktif.
    
    Returns:
        bool: True jika virtual environment aktif
    """
    # Metode 1: Cek environment variable
    if os.environ.get('VIRTUAL_ENV'):
        return True
    
    # Metode 2: Cek jika prefix berbeda
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True
    
    # Metode 3: Cek jika ada folder venv di dekat sys.executable
    venv_path = os.path.dirname(os.path.dirname(sys.executable))
    if "venv" in sys.executable.lower() or os.path.exists(os.path.join(venv_path, "pyvenv.cfg")):
        return True
    
    return False


def create_venv(python_exec: str = None, force: bool = False) -> bool:
    """
    Membuat virtual environment baru menggunakan venv module.
    
    Args:
        python_exec (str): Path ke executable Python yang akan digunakan
        force (bool): Force recreate jika venv sudah ada
    
    Returns:
        bool: True jika berhasil
    """
    venv_dir = venv_path()
    
    # Cek apakah venv sudah ada
    if os.path.exists(venv_dir):
        if not force:
            print("[i] Virtual environment sudah ada.")
            return True
        else:
            print("[i] Menghapus virtual environment lama...")
            import shutil
            try:
                shutil.rmtree(venv_dir)
            except Exception as e:
                print(f"[!] Gagal menghapus venv lama: {e}")
                return False
    
    # Tentukan python executable
    if python_exec is None:
        python_exec = detect_python_executable()
    
    print(f"[+] Membuat Virtual Environment dengan {python_exec}...")
    
    try:
        # Gunakan module venv
        result = subprocess.run(
            [python_exec, "-m", "venv", venv_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"[!] Gagal membuat venv: {result.stderr}")
            
            # Fallback: coba dengan virtualenv jika tersedia
            if is_command_available("virtualenv"):
                print("[i] Mencoba dengan virtualenv...")
                result = subprocess.run(
                    ["virtualenv", venv_dir],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"[!] Gagal dengan virtualenv: {result.stderr}")
                    return False
        
        # Verifikasi venv dibuat
        if os.path.exists(venv_dir):
            print(f"[✓] Virtual environment dibuat di: {venv_dir}")
            return True
        else:
            print("[!] Virtual environment gagal dibuat.")
            return False
            
    except subprocess.TimeoutExpired:
        print("[!] Timeout saat membuat virtual environment")
        return False
    except Exception as e:
        print(f"[!] Error membuat virtual environment: {e}")
        return False


def upgrade_pip(venv_python: str) -> bool:
    """
    Upgrade pip, setuptools, dan wheel di virtual environment.
    
    Args:
        venv_python (str): Path ke Python di virtual environment
    
    Returns:
        bool: True jika berhasil
    """
    print("[+] Upgrade pip, setuptools, dan wheel...")
    
    try:
        packages = ["pip", "setuptools", "wheel"]
        for package in packages:
            result = subprocess.run(
                [venv_python, "-m", "pip", "install", "--upgrade", package],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"[!] Gagal mengupgrade {package}: {result.stderr[:200]}")
                return False
        
        print("[✓] pip, setuptools, dan wheel sudah terupdate")
        return True
        
    except subprocess.TimeoutExpired:
        print("[!] Timeout saat mengupgrade pip")
        return False
    except Exception as e:
        print(f"[!] Error mengupgrade pip: {e}")
        return False


def install_requirements(venv_python: str = None, requirements_file: str = None) -> bool:
    """
    Menginstall dependencies dari requirements.txt menggunakan pip di virtual environment.
    
    Args:
        venv_python (str): Path ke executable Python dalam virtual environment
        requirements_file (str): Path ke file requirements.txt
    
    Returns:
        bool: True jika berhasil
    """
    proj_root = project_root()
    
    # Tentukan file requirements
    if requirements_file is None:
        requirements_file = os.path.join(proj_root, "requirements.txt")
    
    # Cek apakah file requirements.txt ada
    if not os.path.exists(requirements_file):
        print(f"[!] requirements.txt tidak ditemukan di: {requirements_file}")
        
        # Coba cari file requirements
        possible_locations = [
            proj_root,
            os.path.join(proj_root, "requirements"),
            os.path.dirname(__file__),
        ]
        
        for location in possible_locations:
            for filename in ["requirements.txt", "requirements-dev.txt", "requirements-prod.txt"]:
                candidate = os.path.join(location, filename)
                if os.path.exists(candidate):
                    requirements_file = candidate
                    print(f"[i] Menggunakan requirements file: {requirements_file}")
                    break
        
        if not os.path.exists(requirements_file):
            print("[!] Tidak dapat menemukan file requirements apapun.")
            return False
    
    # Tentukan venv_python
    if venv_python is None:
        venv_python = get_python_in_venv()
        if venv_python is None:
            print("[!] Tidak dapat menemukan Python di virtual environment")
            print("[i] Mencoba membuat virtual environment...")
            if not create_venv():
                return False
            venv_python = get_python_in_venv()
            if venv_python is None:
                return False
    
    # Upgrade pip dulu
    if not upgrade_pip(venv_python):
        print("[!] Gagal mengupgrade pip, melanjutkan dengan pip yang ada...")
    
    # Install dependencies
    print(f"[+] Install dependencies dari {requirements_file} ...")
    
    try:
        result = subprocess.run(
            [venv_python, "-m", "pip", "install", "-r", requirements_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 menit timeout
        )
        
        if result.returncode != 0:
            print(f"[!] Gagal menginstall dependencies: {result.stderr[:500]}")
            
            # Coba dengan --no-cache-dir jika gagal
            print("[i] Mencoba tanpa cache...")
            result = subprocess.run(
                [venv_python, "-m", "pip", "install", "--no-cache-dir", "-r", requirements_file],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"[!] Masih gagal: {result.stderr[:500]}")
                return False
        
        # Tampilkan package yang diinstall
        print("[+] Dependencies berhasil diinstall")
        
        # Tampilkan versi yang diinstall
        print("[i] Menampilkan package yang terinstall...")
        subprocess.run(
            [venv_python, "-m", "pip", "list"],
            capture_output=False,
            timeout=30
        )
        
        return True
        
    except subprocess.TimeoutExpired:
        print("[!] Timeout saat menginstall dependencies")
        return False
    except Exception as e:
        print(f"[!] Error menginstall dependencies: {e}")
        return False


def create_default_requirements():
    """
    Membuat file requirements.txt default jika tidak ada.
    """
    requirements_content = """# BMS Dependencies
Flask==2.3.3
Werkzeug==2.3.7
waitress==2.1.2
gunicorn==20.1.0
psutil==5.9.5
colorama==0.4.6
click==8.1.3
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3

# Development dependencies (optional)
# pytest==7.4.0
# pytest-cov==4.1.0
# black==23.7.0
# flake8==6.0.0
"""
    
    requirements_file = os.path.join(project_root(), "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print("[+] Membuat requirements.txt default...")
        with open(requirements_file, "w") as f:
            f.write(requirements_content)
        print(f"[✓] requirements.txt dibuat di: {requirements_file}")
        return True
    
    return False


def check_venv_health(venv_dir: str = None) -> dict:
    """
    Memeriksa kesehatan virtual environment.
    
    Args:
        venv_dir (str): Path ke virtual environment
    
    Returns:
        dict: Informasi kesehatan venv
    """
    if venv_dir is None:
        venv_dir = venv_path()
    
    health_info = {
        "exists": False,
        "python_found": False,
        "pip_found": False,
        "python_version": None,
        "pip_version": None,
        "is_activated": False,
        "issues": []
    }
    
    # Cek keberadaan folder
    if not os.path.exists(venv_dir):
        health_info["issues"].append("Folder venv tidak ditemukan")
        return health_info
    
    health_info["exists"] = True
    
    # Cek Python executable
    python_exe = get_python_in_venv(venv_dir)
    if python_exe:
        health_info["python_found"] = True
        
        # Dapatkan versi Python
        try:
            result = subprocess.run(
                [python_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                health_info["python_version"] = result.stdout.strip()
        except:
            health_info["issues"].append("Tidak bisa mendapatkan versi Python")
    else:
        health_info["issues"].append("Python executable tidak ditemukan di venv")
    
    # Cek pip
    if python_exe:
        try:
            result = subprocess.run(
                [python_exe, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                health_info["pip_found"] = True
                lines = result.stdout.strip().split('\n')
                if lines:
                    health_info["pip_version"] = lines[0]
        except:
            health_info["issues"].append("Tidak bisa mendapatkan versi pip")
    
    # Cek jika venv aktif
    health_info["is_activated"] = is_venv_active()
    
    return health_info


def setup_environment(python_exec: str = None, force_recreate: bool = False) -> bool:
    """
    Setup lengkap environment: buat venv, install dependencies.
    
    Args:
        python_exec (str): Python executable yang akan digunakan
        force_recreate (bool): Force recreate venv
    
    Returns:
        bool: True jika berhasil
    """
    print("=" * 60)
    print("SETUP BMS ENVIRONMENT")
    print("=" * 60)
    
    # Cek jika requirements.txt ada, buat default jika tidak
    req_file = os.path.join(project_root(), "requirements.txt")
    if not os.path.exists(req_file):
        create_default_requirements()
    
    # Cek kesehatan venv
    health = check_venv_health()
    
    if health["exists"] and not force_recreate:
        print("[i] Virtual environment sudah ada.")
        if health["python_found"] and health["pip_found"]:
            print(f"[i] Python: {health.get('python_version', 'unknown')}")
            print(f"[i] Pip: {health.get('pip_version', 'unknown')}")
            
            # Tanya user apakah ingin recreate
            if force_recreate:
                recreate = True
            else:
                try:
                    response = input("[?] Recreate virtual environment? (y/N): ").strip().lower()
                    recreate = response in ['y', 'yes']
                except (KeyboardInterrupt, EOFError):
                    print("\n[i] Dibatalkan")
                    return False
        else:
            print("[!] Venv tidak sehat, akan dibuat ulang...")
            recreate = True
    else:
        recreate = True
    
    # Buat/recreate venv
    if recreate:
        if not create_venv(python_exec, force=True):
            return False
    
    # Dapatkan Python dari venv
    venv_python = get_python_in_venv()
    if venv_python is None:
        print("[!] Gagal mendapatkan Python dari venv")
        return False
    
    # Install requirements
    if not install_requirements(venv_python):
        print("[!] Gagal menginstall requirements")
        return False
    
    # Verifikasi setup
    health = check_venv_health()
    if health["python_found"] and health["pip_found"]:
        print("\n" + "=" * 60)
        print("✅ SETUP SELESAI")
        print("=" * 60)
        print(f"Python: {health.get('python_version', 'unknown')}")
        print(f"Pip: {health.get('pip_version', 'unknown')}")
        print(f"Venv: {venv_path()}")
        print("=" * 60)
        return True
    else:
        print("\n[!] Setup gagal")
        return False


if __name__ == "__main__":
    # Mode testing
    import argparse
    
    parser = argparse.ArgumentParser(description="BMS Environment Tools")
    parser.add_argument("--check", action="store_true", help="Cek kesehatan environment")
    parser.add_argument("--setup", action="store_true", help="Setup environment")
    parser.add_argument("--recreate", action="store_true", help="Force recreate venv")
    parser.add_argument("--python", help="Path ke Python executable")
    
    args = parser.parse_args()
    
    if args.check:
        health = check_venv_health()
        print("\nVENV HEALTH CHECK:")
        print(f"  Exists: {health['exists']}")
        print(f"  Python found: {health['python_found']}")
        print(f"  Pip found: {health['pip_found']}")
        print(f"  Python version: {health['python_version']}")
        print(f"  Pip version: {health['pip_version']}")
        print(f"  Is activated: {health['is_activated']}")
        if health['issues']:
            print(f"  Issues: {', '.join(health['issues'])}")
    
    elif args.setup:
        setup_environment(args.python, args.recreate)
    
    else:
        print("BMS Environment Tools")
        print(f"Project root: {project_root()}")
        print(f"Venv path: {venv_path()}")
        print(f"Python in venv: {get_python_in_venv()}")
        print(f"Is venv active: {is_venv_active()}")