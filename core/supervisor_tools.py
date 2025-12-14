# core/supervisor_tools.py
import os
from core.system_tools import run

def setup_supervisor(env: dict, project_dir: str, venv_python: str):
    """
    Mengkonfigurasi dan mengatur Supervisor untuk menjalankan aplikasi BMS.
    Hanya berjalan pada sistem Linux.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Key yang digunakan: 'os' untuk memeriksa sistem operasi.
        project_dir (str): Path ke direktori root proyek.
        venv_python (str): Path ke executable Python di dalam virtual environment.
    """
    if env.get("os") != "linux":
        print("[!] Supervisor hanya tersedia di Linux.")
        return

    # Buat folder logs jika belum ada
    LOG_DIR = os.path.join(project_dir, "logs")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print("[+] Folder logs dibuat:", LOG_DIR)

    # Path untuk file konfigurasi Supervisor
    conf_path = "/etc/supervisor/conf.d/BMS.conf"

    # Template konfigurasi Supervisor untuk aplikasi BMS
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
    
    # Tulis konfigurasi ke file sementara
    tmp = "BMS_supervisor_temp.conf"
    with open(tmp, "w") as f:
        f.write(config)

    # Salin konfigurasi ke direktori Supervisor
    print("[+] Menyalin konfigurasi supervisor ke /etc/supervisor/conf.d/ ...")
    run(f"sudo cp {tmp} {conf_path}")
    
    # Hapus file sementara
    os.remove(tmp)

    # Terapkan konfigurasi Supervisor
    print("[+] Reload supervisor & start process BMS ...")
    run("sudo supervisorctl reread")  # Baca ulang konfigurasi
    run("sudo supervisorctl update")   # Perbarui proses yang dikelola
    run("sudo supervisorctl restart BMS")  # Restart service BMS
    print("[✓] Supervisor terkonfigurasi.")