# core/repair_tools.py
import os
from core.system_tools import run

def repair_gunicorn():
    """
    Memperbaiki masalah Gunicorn dengan menghentikan semua proses Gunicorn yang berjalan
    dan menghapus file PID jika ada.
    Fungsi ini aman untuk dijalankan bahkan jika tidak ada proses Gunicorn yang berjalan.
    """
    print("[i] Memperbaiki Gunicorn...")
    # Menghentikan semua proses Gunicorn dengan graceful kill
    run("pkill gunicorn || true")
    
    # Menghapus file PID Gunicorn jika ada (untuk mencegah konflik)
    if os.path.exists("/tmp/gunicorn.pid"):
        run("sudo rm -f /tmp/gunicorn.pid")
    print("[✓] Gunicorn diperbaiki.")

def repair_port_5000(env):
    """
    Membersihkan port 5000 dengan menghentikan proses yang menggunakan port tersebut.
    Menggunakan metode yang berbeda berdasarkan sistem operasi:
    - Linux: menggunakan fuser
    - Non-Linux: menggunakan lsof (jika tersedia)
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    """
    print("[i] Membersihkan port 5000...")
    if env.get("os") == "linux":
        # Gunakan fuser untuk membunuh proses yang menggunakan port 5000 pada Linux
        run("sudo fuser -k 5000/tcp || true")
    else:
        # Fallback untuk sistem POSIX lain (macOS, BSD) menggunakan lsof
        run("kill -9 $(lsof -t -i:5000) || true")
    print("[✓] Port 5000 dibersihkan.")

def repair_supervisor(env):
    """
    Memperbaiki konfigurasi Supervisor dengan:
    1. Membaca ulang konfigurasi
    2. Memperbarui proses
    3. Restart service BMS
    
    Hanya berjalan pada sistem Linux yang memiliki Supervisor.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    """
    if env.get("os") != "linux":
        print("[!] Supervisor tidak tersedia di OS ini.")
        return
    
    print("[i] Memperbaiki Supervisor...")
    # Membaca ulang konfigurasi Supervisor
    run("sudo supervisorctl reread || true")
    
    # Memperbarui daftar proses Supervisor
    run("sudo supervisorctl update || true")
    
    # Restart service BMS di Supervisor
    run("sudo supervisorctl restart BMS || true")
    print("[✓] Supervisor diperbaiki.")

def repair_nginx(env):
    """
    Memperbaiki Nginx dengan:
    1. Menguji konfigurasi Nginx
    2. Merestart service Nginx
    
    Hanya berjalan pada sistem Linux.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    """
    if env.get("os") != "linux":
        print("[!] Nginx hanya tersedia di Linux.")
        return
    
    print("[i] Memeriksa konfigurasi Nginx...")
    # Menguji konfigurasi Nginx untuk memastikan valid
    run("sudo nginx -t || true")
    
    print("[i] Restart Nginx...")
    # Merestart service Nginx untuk menerapkan perubahan
    run("sudo systemctl restart nginx || true")
    print("[✓] Nginx diperbaiki.")

def repair_permissions(project_dir: str):
    """
    Memperbaiki permission folder project dengan menetapkan mode 755 secara rekursif.
    
    Args:
        project_dir (str): Path ke direktori root proyek.
    """
    print("[i] Menyetel ulang permission folder project...")
    # Menetapkan permission 755 (rwxr-xr-x) untuk semua file dan folder
    run(f"sudo chmod -R 755 {project_dir} || true")
    print("[✓] Permission diperbaiki.")

def auto_repair(env: dict, project_dir: str):
    """
    Menjalankan semua fungsi perbaikan secara berurutan untuk memperbaiki sistem BMS.
    Urutan perbaikan:
    1. Gunicorn
    2. Port 5000
    3. Supervisor
    4. Nginx
    5. Permission folder project
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
        project_dir (str): Path ke direktori root proyek.
    """
    print("====== BMS AUTO REPAIR ======")
    repair_gunicorn()
    repair_port_5000(env)
    repair_supervisor(env)
    repair_nginx(env)
    repair_permissions(project_dir)
    print("====== PERBAIKAN SELESAI ======")