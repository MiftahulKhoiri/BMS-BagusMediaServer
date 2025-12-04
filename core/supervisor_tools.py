# core/supervisor_tools.py
import os
from core.system_tools import run

def setup_supervisor(env: dict, project_dir: str, venv_python: str):
    if env.get("os") != "linux":
        print("[!] Supervisor hanya tersedia di Linux.")
        return

    LOG_DIR = os.path.join(project_dir, "logs")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print("[+] Folder logs dibuat:", LOG_DIR)

    conf_path = "/etc/supervisor/conf.d/BMS.conf"

    config = f"""
[program:BMS]
directory={project_dir}
command={venv_python} -m gunicorn -w 3 --threads 3 -b 127.0.0.1:5000 app:create_app()
autostart=true
autorestart=true
stderr_logfile={LOG_DIR}/gunicorn_err.log
stdout_logfile={LOG_DIR}/gunicorn_out.log
environment=PATH="{os.path.join(project_dir, 'venv', 'bin')}"
"""
    tmp = "BMS_supervisor_temp.conf"
    with open(tmp, "w") as f:
        f.write(config)

    print("[+] Menyalin konfigurasi supervisor ke /etc/supervisor/conf.d/ ...")
    run(f"sudo cp {tmp} {conf_path}")
    os.remove(tmp)

    print("[+] Reload supervisor & start process BMS ...")
    run("sudo supervisorctl reread")
    run("sudo supervisorctl update")
    run("sudo supervisorctl restart BMS")
    print("[✓] Supervisor terkonfigurasi.")