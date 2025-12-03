# core/repair_tools.py
import os
from core.system_tools import run

def repair_gunicorn():
    print("[i] Memperbaiki Gunicorn...")
    run("pkill gunicorn || true")
    if os.path.exists("/tmp/gunicorn.pid"):
        run("sudo rm -f /tmp/gunicorn.pid")
    print("[✓] Gunicorn diperbaiki.")

def repair_port_5000(env):
    print("[i] Membersihkan port 5000...")
    if env.get("os") == "linux":
        run("sudo fuser -k 5000/tcp || true")
    else:
        # best-effort: try lsof-based kill on POSIX
        run("kill -9 $(lsof -t -i:5000) || true")
    print("[✓] Port 5000 dibersihkan.")

def repair_supervisor(env):
    if env.get("os") != "linux":
        print("[!] Supervisor tidak tersedia di OS ini.")
        return
    print("[i] Memperbaiki Supervisor...")
    run("sudo supervisorctl reread || true")
    run("sudo supervisorctl update || true")
    run("sudo supervisorctl restart BMS || true")
    print("[✓] Supervisor diperbaiki.")

def repair_nginx(env):
    if env.get("os") != "linux":
        print("[!] Nginx hanya tersedia di Linux.")
        return
    print("[i] Memeriksa konfigurasi Nginx...")
    run("sudo nginx -t || true")
    print("[i] Restart Nginx...")
    run("sudo systemctl restart nginx || true")
    print("[✓] Nginx diperbaiki.")

def repair_permissions(project_dir: str):
    print("[i] Menyetel ulang permission folder project...")
    run(f"sudo chmod -R 755 {project_dir} || true")
    print("[✓] Permission diperbaiki.")

def auto_repair(env: dict, project_dir: str):
    print("====== BMS AUTO REPAIR ======")
    repair_gunicorn()
    repair_port_5000(env)
    repair_supervisor(env)
    repair_nginx(env)
    repair_permissions(project_dir)
    print("====== PERBAIKAN SELESAI ======")