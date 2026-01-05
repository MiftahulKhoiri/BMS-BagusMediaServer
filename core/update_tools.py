# core/update_tools.py
import os
import shutil
import subprocess
from core.system_tools import run
from core.env_tools import get_python_in_venv


def git_available():
    """
    Mengecek apakah Git tersedia di sistem.
    
    Returns:
        bool: True jika git tersedia, False jika tidak.
    """
    return shutil.which("git") is not None


def git_pull(project_dir: str) -> bool:
    """
    Menjalankan git pull di direktori project.
    
    Args:
        project_dir (str): Path ke direktori root proyek.
    
    Returns:
        bool: True jika git pull berhasil, False jika gagal.
    """
    print("[i] Menarik update dari Git (git pull)...")

    if not git_available():
        print("[!] Git tidak ditemukan di sistem.")
        return False

    cur = os.getcwd()
    try:
        os.chdir(project_dir)
        # Jalankan git pull dan ambil exit code
        result = subprocess.run(["git", "pull"], 
                              capture_output=True, 
                              text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Gagal menjalankan git pull: {e}")
        return False
    finally:
        os.chdir(cur)


def has_requirements(project_dir: str) -> bool:
    """
    Mengecek apakah file requirements.txt ada.
    
    Args:
        project_dir (str): Path ke direktori root proyek.
    
    Returns:
        bool: True jika requirements.txt ada, False jika tidak.
    """
    return os.path.exists(os.path.join(project_dir, "requirements.txt"))


def restart_services(env: dict):
    """
    Restart service yang terkait dengan aplikasi BMS.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
    """
    print("[i] Restarting services (if applicable)...")

    if env.get("os") == "linux":
        run("pkill gunicorn || true")
        run("sudo supervisorctl restart BMS || true")
    else:
        print("[i] Bukan Linux. Restart manual jika diperlukan.")

    print("[✓] Restart selesai.")


def auto_update(env: dict, project_dir: str):
    """
    Melakukan update standar dengan git pull dan install dependencies.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
        project_dir (str): Path ke direktori root proyek.
    """
    print("====== BMS AUTO UPDATE ======")

    if not git_pull(project_dir):
        print("[!] Git pull gagal. Update dibatalkan.")
        return

    # Install dependencies jika ada requirements.txt
    if has_requirements(project_dir):
        venv_py = get_python_in_venv()
        if venv_py:
            print("[i] Menyinkronkan dependencies...")
            run(f"{venv_py} -m pip install -r {os.path.join(project_dir, 'requirements.txt')}")
        else:
            print("[!] venv tidak ditemukan.")

    restart_services(env)
    print("====== UPDATE SELESAI ======")


def force_update(env: dict, project_dir: str):
    """
    Melakukan force update dengan menghapus semua perubahan lokal.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
        project_dir (str): Path ke direktori root proyek.
    """
    print("====== BMS FORCE UPDATE ======")
    print("[!] PERINGATAN: Semua perubahan lokal AKAN DIHAPUS.")
    print("[!] Folder project akan disamakan 100% dengan GitHub.\n")

    if not git_available():
        print("[!] Git tidak tersedia. Tidak dapat melakukan Force Update.")
        return

    cur = os.getcwd()
    try:
        os.chdir(project_dir)

        print("[+] Reset perubahan lokal...")
        subprocess.run(["git", "reset", "--hard", "HEAD"], 
                      capture_output=True, text=True)

        print("[+] Membersihkan file yang tidak ter-tracked...")
        subprocess.run(["git", "clean", "-fd"], 
                      capture_output=True, text=True)

        print("[+] Menarik update terbaru...")
        result = subprocess.run(["git", "pull"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print("[!] Gagal menarik update GitHub.")
            return

    except Exception as e:
        print(f"[ERROR] Gagal melakukan force update: {e}")
        return
    finally:
        os.chdir(cur)

    # Install ulang dependencies
    if has_requirements(project_dir):
        venv_py = get_python_in_venv()
        if venv_py:
            print("[i] Install ulang semua dependencies...")
            run(f"{venv_py} -m pip install -r {os.path.join(project_dir, 'requirements.txt')}")
        else:
            print("[!] venv tidak ditemukan.")

    restart_services(env)
    print("====== FORCE UPDATE SELESAI ======")