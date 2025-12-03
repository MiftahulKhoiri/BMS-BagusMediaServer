# core/update_tools.py
import os
import shutil
from core.system_tools import run
from core.env_tools import get_python_in_venv

def git_available():
    return shutil.which("git") is not None

def git_pull(project_dir: str):
    print("[i] Menarik update dari Git (git pull)...")
    if not git_available():
        print("[!] Git tidak tersedia di sistem.")
        return False
    # jalankan di folder project
    cur = os.getcwd()
    try:
        os.chdir(project_dir)
        status = run("git pull")
        return status == 0
    finally:
        os.chdir(cur)

def has_requirements(project_dir: str):
    return os.path.exists(os.path.join(project_dir, "requirements.txt"))

def restart_services(env: dict):
    print("[i] Restarting services (if applicable)...")
    if env.get("os") == "linux":
        run("pkill gunicorn")
        run("sudo supervisorctl restart BMS")
    else:
        print("[i] Non-Linux: restart manual jika perlu.")
    print("[✓] Restart attempts selesai.")

def auto_update(env: dict, project_dir: str):
    print("====== BMS AUTO UPDATE ======")
    if not git_pull(project_dir):
        print("[!] Git pull gagal. Update dibatalkan.")
        return

    if has_requirements(project_dir):
        venv_py = get_python_in_venv()
        print("[i] Menginstall ulang/menyinkronkan dependencies...")
        run(f"{venv_py} -m pip install -r {os.path.join(project_dir, 'requirements.txt')}")
    restart_services(env)
    print("====== UPDATE SELESAI ======")