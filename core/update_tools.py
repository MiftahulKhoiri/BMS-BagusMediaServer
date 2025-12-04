# core/update_tools.py
import os
import shutil
from core.system_tools import run
from core.env_tools import get_python_in_venv


# ===========================================================
# 1. CEK APAKAH GIT TERSEDIA
# ===========================================================
def git_available():
    """Return True jika git tersedia di sistem."""
    return shutil.which("git") is not None


# ===========================================================
# 2. FUNGSI GIT PULL NORMAL
# ===========================================================
def git_pull(project_dir: str) -> bool:
    """Menjalankan git pull di direktori project."""
    
    print("[i] Menarik update dari Git (git pull)...")

    if not git_available():
        print("[!] Git tidak ditemukan di sistem.")
        return False

    cur = os.getcwd()
    try:
        os.chdir(project_dir)
        status = run("git pull")
        return status == 0
    finally:
        os.chdir(cur)


# ===========================================================
# 3. CEK REQUIREMENTS.TXT
# ===========================================================
def has_requirements(project_dir: str) -> bool:
    """Cek apakah requirements.txt ada."""
    return os.path.exists(os.path.join(project_dir, "requirements.txt"))


# ===========================================================
# 4. RESTART SERVICES (GUNICORN / SUPERVISOR / DLL)
# ===========================================================
def restart_services(env: dict):
    """Restart service sesuai OS."""
    
    print("[i] Restarting services (if applicable)...")

    if env.get("os") == "linux":
        run("pkill gunicorn")
        run("sudo supervisorctl restart BMS")
    else:
        print("[i] Bukan Linux. Restart manual jika diperlukan.")

    print("[✓] Restart selesai.")


# ===========================================================
# 5. AUTO UPDATE STANDARD
# ===========================================================
def auto_update(env: dict, project_dir: str):
    """Update normal (tidak menghapus perubahan lokal)."""
    
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


# ===========================================================
# 6. FORCE UPDATE (HAPUS PERUBAHAN LOKAL)
# ===========================================================
def force_update(env: dict, project_dir: str):
    """
    Force update:
    - Menghapus semua perubahan lokal
    - Membersihkan file yang tidak ada di GitHub
    - Menarik ulang versi GitHub
    - Install dependencies
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
        run("git reset --hard HEAD")

        print("[+] Membersihkan file yang tidak ter-tracked...")
        run("git clean -fd")

        print("[+] Menarik update terbaru...")
        if run("git pull") != 0:
            print("[!] Gagal menarik update GitHub.")
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