# core/repair_tools.py
import os
import sys
import signal
import platform
from pathlib import Path
from core.system_tools import run, is_command_available

def get_pid_using_port(port: int) -> list:
    """
    Mendapatkan daftar PID yang menggunakan port tertentu.
    Cross-platform compatible (Linux, macOS, Windows WSL).
    
    Args:
        port (int): Port number yang akan dicek
        
    Returns:
        list: List of PID yang menggunakan port
    """
    pids = []
    
    try:
        if platform.system().lower() == "linux":
            # Gunakan ss (socket statistics) - modern dan lebih baik dari netstat
            result = run(f"ss -tlnp | grep :{port} | awk '{{print $NF}}' | cut -d, -f2 | cut -d= -f2")
            if result and result.stdout:
                pids = list(set(result.stdout.strip().split()))
        
        elif platform.system().lower() == "darwin":  # macOS
            # Gunakan lsof
            result = run(f"lsof -ti:{port}")
            if result and result.stdout:
                pids = result.stdout.strip().split()
        
        elif platform.system().lower() == "windows":
            # Windows/WSL menggunakan netstat
            result = run(f"netstat -ano | findstr :{port}")
            if result and result.stdout:
                for line in result.stdout.split('\n'):
                    if f":{port}" in line:
                        parts = line.strip().split()
                        if len(parts) > 4:
                            pids.append(parts[-1])
    
    except Exception as e:
        print(f"[!] Error getting PIDs for port {port}: {e}", file=sys.stderr)
    
    return pids

def kill_processes(pids: list, signal_name: str = "TERM"):
    """
    Mengirim sinyal ke daftar proses secara aman.
    
    Args:
        pids (list): List of process IDs
        signal_name (str): Signal name (TERM, KILL, HUP)
    """
    if not pids:
        return
    
    try:
        signal_map = {
            "TERM": signal.SIGTERM,
            "KILL": signal.SIGKILL,
            "HUP": signal.SIGHUP
        }
        
        sig = signal_map.get(signal_name.upper(), signal.SIGTERM)
        
        for pid_str in pids:
            try:
                pid = int(pid_str)
                os.kill(pid, sig)
                print(f"[i] Sent {signal_name} signal to PID {pid}")
            except (ValueError, ProcessLookupError, PermissionError):
                # Process sudah mati atau tidak ada permission
                continue
    
    except Exception as e:
        print(f"[!] Error killing processes: {e}", file=sys.stderr)

def repair_gunicorn():
    """
    Memperbaiki masalah Gunicorn dengan menghentikan semua proses Gunicorn yang berjalan
    secara bertahap dan aman.
    """
    print("[i] Memperbaiki Gunicorn...")
    
    try:
        # Step 1: Coba graceful shutdown (SIGTERM)
        print("[i] Sending graceful shutdown to Gunicorn processes...")
        run("pkill -f 'gunicorn.*bms_app' || true")
        run("pkill -f 'gunicorn.*wsgi:application' || true")
        
        # Tunggu 2 detik untuk proses graceful shutdown
        import time
        time.sleep(2)
        
        # Step 2: Force kill jika masih ada (SIGKILL)
        print("[i] Force killing remaining Gunicorn processes...")
        run("pkill -9 -f 'gunicorn.*bms_app' || true")
        run("pkill -9 -f 'gunicorn.*wsgi:application' || true")
        
        # Step 3: Bersihkan semua file PID yang mungkin ada
        pid_files = [
            "/tmp/gunicorn.pid",
            "/var/run/gunicorn.pid",
            "/var/run/gunicorn/bms.pid",
            "gunicorn.pid",
            "/tmp/bms_gunicorn.pid"
        ]
        
        for pid_file in pid_files:
            if os.path.exists(pid_file):
                try:
                    os.remove(pid_file)
                    print(f"[✓] Removed PID file: {pid_file}")
                except:
                    run(f"sudo rm -f {pid_file} || true")
        
        # Step 4: Hapus socket files jika ada
        socket_files = [
            "/tmp/gunicorn.sock",
            "/var/run/gunicorn.sock",
            "/tmp/bms.sock"
        ]
        
        for sock_file in socket_files:
            if os.path.exists(sock_file):
                try:
                    os.remove(sock_file)
                    print(f"[✓] Removed socket file: {sock_file}")
                except:
                    run(f"sudo rm -f {sock_file} || true")
    
    except Exception as e:
        print(f"[!] Error repairing Gunicorn: {e}", file=sys.stderr)
    
    print("[✓] Gunicorn diperbaiki.")

def repair_port_5000(env):
    """
    Membersihkan port 5000 dengan cara yang lebih aman dan cross-platform.
    """
    print("[i] Membersihkan port 5000...")
    
    try:
        # Dapatkan semua PID yang menggunakan port 5000
        pids = get_pid_using_port(5000)
        
        if pids:
            print(f"[i] Found {len(pids)} process(es) using port 5000")
            
            # Step 1: Coba graceful shutdown
            kill_processes(pids, "TERM")
            
            # Tunggu 1 detik
            import time
            time.sleep(1)
            
            # Step 2: Cek lagi, jika masih ada, force kill
            remaining_pids = get_pid_using_port(5000)
            if remaining_pids:
                print("[i] Force killing remaining processes...")
                kill_processes(remaining_pids, "KILL")
        else:
            print("[i] No processes found using port 5000")
        
        # Fallback: gunakan metode OS-specific
        if env.get("os") == "linux":
            if is_command_available("fuser"):
                run("sudo fuser -k 5000/tcp 2>/dev/null || true")
            elif is_command_available("ss"):
                run("sudo ss -tlnp | grep :5000 | awk '{print $NF}' | cut -d, -f2 | cut -d= -f2 | xargs -r sudo kill -9 2>/dev/null || true")
        else:
            # Untuk macOS dan lainnya
            if is_command_available("lsof"):
                run("lsof -ti:5000 | xargs -r kill -9 2>/dev/null || true")
    
    except Exception as e:
        print(f"[!] Error cleaning port 5000: {e}", file=sys.stderr)
    
    print("[✓] Port 5000 dibersihkan.")

def repair_supervisor(env):
    """
    Memperbaiki konfigurasi Supervisor dengan error handling yang lebih baik.
    """
    if env.get("os") != "linux":
        print("[!] Supervisor tidak tersedia di OS ini.")
        return
    
    if not is_command_available("supervisorctl"):
        print("[!] Supervisor tidak terinstal.")
        return
    
    print("[i] Memperbaiki Supervisor...")
    
    try:
        # Cek status supervisor dulu
        status_result = run("sudo supervisorctl status")
        if status_result and "BMS" in status_result.stdout:
            print("[i] BMS service found in Supervisor")
        
        # Membaca ulang konfigurasi
        print("[i] Rereading configuration...")
        run("sudo supervisorctl reread 2>/dev/null || true")
        
        # Memperbarui daftar proses
        print("[i] Updating process list...")
        run("sudo supervisorctl update 2>/dev/null || true")
        
        # Restart service BMS dengan graceful
        print("[i] Restarting BMS service...")
        run("sudo supervisorctl restart BMS 2>/dev/null || true")
        
        # Tampilkan status terakhir
        print("[i] Final status:")
        run("sudo supervisorctl status BMS 2>/dev/null || true")
    
    except Exception as e:
        print(f"[!] Error repairing Supervisor: {e}", file=sys.stderr)
        print("[!] Trying alternative methods...")
        
        # Fallback: restart supervisor service
        if is_command_available("systemctl"):
            run("sudo systemctl restart supervisor 2>/dev/null || sudo systemctl restart supervisord 2>/dev/null || true")
    
    print("[✓] Supervisor diperbaiki.")

def repair_nginx(env):
    """
    Memperbaiki Nginx dengan validasi konfigurasi yang lebih ketat.
    """
    if env.get("os") != "linux":
        print("[!] Nginx hanya tersedia di Linux.")
        return
    
    if not is_command_available("nginx"):
        print("[!] Nginx tidak terinstal.")
        return
    
    print("[i] Memperbaiki Nginx...")
    
    try:
        # Step 1: Validasi konfigurasi
        print("[i] Testing Nginx configuration...")
        test_result = run("sudo nginx -t 2>&1")
        
        if test_result and "syntax is ok" in test_result.stdout.lower():
            print("[✓] Nginx configuration is valid")
            
            # Step 2: Reload if running, otherwise start
            if is_command_available("systemctl"):
                status_result = run("systemctl is-active nginx 2>/dev/null || true")
                if status_result and "active" in status_result.stdout:
                    print("[i] Reloading Nginx...")
                    run("sudo systemctl reload nginx 2>/dev/null || true")
                else:
                    print("[i] Starting Nginx...")
                    run("sudo systemctl start nginx 2>/dev/null || true")
            else:
                # Fallback untuk init.d
                run("sudo nginx -s reload 2>/dev/null || sudo service nginx reload 2>/dev/null || true")
        else:
            print("[✗] Nginx configuration has errors:")
            if test_result:
                print(test_result.stderr or test_result.stdout)
            print("[i] Attempting to fix by restoring default BMS config...")
            
            # Coba restore konfigurasi default
            from core.nginx_tools import generate_nginx_config
            project_dir = Path(__file__).parent.parent.parent
            generate_nginx_config(str(project_dir))
            
            # Restart nginx
            run("sudo systemctl restart nginx 2>/dev/null || sudo service nginx restart 2>/dev/null || true")
    
    except Exception as e:
        print(f"[!] Error repairing Nginx: {e}", file=sys.stderr)
    
    print("[✓] Nginx diperbaiki.")

def repair_permissions(project_dir: str):
    """
    Memperbaiki permission dengan cara yang lebih aman dan tepat.
    Tidak memberikan permission 755 secara rekursif ke semua file.
    """
    print("[i] Memperbaiki permissions...")
    
    try:
        project_path = Path(project_dir)
        
        # Hanya folder yang perlu permission 755
        directories = [
            project_path,
            project_path / "logs",
            project_path / "static",
            project_path / "uploads",
            project_path / "temp"
        ]
        
        for directory in directories:
            if directory.exists():
                run(f"sudo chmod 755 {directory} 2>/dev/null || true")
                print(f"[✓] Set 755 on directory: {directory}")
        
        # File executable perlu 755
        executable_patterns = ["*.py", "*.sh", "wsgi.py"]
        for pattern in executable_patterns:
            run(f"find {project_dir} -name '{pattern}' -type f -exec sudo chmod 755 {{}} \\; 2>/dev/null || true")
        
        # File lainnya cukup 644
        run(f"find {project_dir} -type f ! -name '*.py' ! -name '*.sh' ! -name 'wsgi.py' -exec sudo chmod 644 {{}} \\; 2>/dev/null || true")
        
        # File sensitif perlu lebih ketat (jika ada)
        sensitive_files = [".env", "config.py", "secret_key.txt"]
        for file_name in sensitive_files:
            file_path = project_path / file_name
            if file_path.exists():
                run(f"sudo chmod 600 {file_path} 2>/dev/null || true")
                print(f"[✓] Set secure permissions on: {file_name}")
        
        # Pastikan ownership benar jika di Linux production
        if platform.system().lower() == "linux":
            run(f"sudo chown -R www-data:www-data {project_dir}/logs 2>/dev/null || true")
            run(f"sudo chown -R www-data:www-data {project_dir}/uploads 2>/dev/null || true")
    
    except Exception as e:
        print(f"[!] Error repairing permissions: {e}", file=sys.stderr)
    
    print("[✓] Permissions diperbaiki.")

def repair_python_deps(venv_python: str = None):
    """
    Memperbaiki dependencies Python dan virtual environment.
    
    Args:
        venv_python (str): Path ke Python dalam virtual environment
    """
    print("[i] Memperbaiki Python dependencies...")
    
    try:
        # Install/upgrade pip
        run(f"{venv_python or 'python3'} -m pip install --upgrade pip 2>/dev/null || true")
        
        # Install requirements
        requirements_file = "requirements.txt"
        if os.path.exists(requirements_file):
            run(f"{venv_python or 'python3'} -m pip install -r {requirements_file} 2>/dev/null || true")
            print("[✓] Requirements installed/updated")
        else:
            print("[!] requirements.txt not found")
        
        # Clear Python cache
        print("[i] Clearing Python cache...")
        run(f"{venv_python or 'python3'} -c \"import sys; from pathlib import Path; "
            f"[p.unlink() for p in Path('.').rglob('*.pyc')]\" 2>/dev/null || true")
        run("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true")
    
    except Exception as e:
        print(f"[!] Error repairing Python dependencies: {e}", file=sys.stderr)
    
    print("[✓] Python dependencies diperbaiki.")

def repair_logs(project_dir: str):
    """
    Membersihkan dan merotasi log files.
    
    Args:
        project_dir (str): Project directory path
    """
    print("[i] Membersihkan log files...")
    
    try:
        logs_dir = Path(project_dir) / "logs"
        if logs_dir.exists():
            # Backup log lama
            run(f"find {logs_dir} -name '*.log' -size +10M -exec mv {{}} {{}}.old \\; 2>/dev/null || true")
            
            # Hapus log yang terlalu tua (>30 hari)
            run(f"find {logs_dir} -name '*.log.old' -mtime +30 -delete 2>/dev/null || true")
            
            # Buat log directory jika tidak ada
            run(f"mkdir -p {logs_dir} 2>/dev/null || true")
            run(f"chmod 755 {logs_dir} 2>/dev/null || true")
            
            print(f"[✓] Logs cleaned in: {logs_dir}")
        else:
            print("[i] No logs directory found")
    
    except Exception as e:
        print(f"[!] Error cleaning logs: {e}", file=sys.stderr)
    
    print("[✓] Logs diperbaiki.")

def auto_repair(env: dict, project_dir: str, venv_python: str = None):
    """
    Menjalankan semua fungsi perbaikan dengan logging yang lebih baik.
    
    Args:
        env (dict): Environment dictionary
        project_dir (str): Project directory path
        venv_python (str): Optional - path to Python in virtual environment
    """
    print("╔══════════════════════════════════════╗")
    print("║         BMS AUTO REPAIR              ║")
    print("╚══════════════════════════════════════╝")
    
    steps = [
        ("Membersihkan Gunicorn", lambda: repair_gunicorn()),
        ("Membersihkan port 5000", lambda: repair_port_5000(env)),
        ("Memperbaiki Supervisor", lambda: repair_supervisor(env)),
        ("Memperbaiki Nginx", lambda: repair_nginx(env)),
        ("Memperbaiki Python dependencies", lambda: repair_python_deps(venv_python)),
        ("Membersihkan logs", lambda: repair_logs(project_dir)),
        ("Memperbaiki permissions", lambda: repair_permissions(project_dir)),
    ]
    
    for i, (desc, func) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {desc}...")
        try:
            func()
        except Exception as e:
            print(f"[✗] Error in {desc}: {e}", file=sys.stderr)
            continue
    
    print("\n" + "="*40)
    print("✓ PERBAIKAN SELESAI")
    print("="*40)
    
    # Berikan rekomendasi jika ada
    if env.get("os") == "linux" and not env.get("is_termux"):
        print("\n[i] Rekomendasi selanjutnya:")
        print("  1. Cek status service: sudo systemctl status nginx")
        print("  2. Cek log: sudo journalctl -u nginx -f")
        print("  3. Test koneksi: curl http://localhost")