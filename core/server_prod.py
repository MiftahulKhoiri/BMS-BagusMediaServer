# core/server_prod.py

import socket
import sys
from core.nginx_tools import generate_nginx_config, reload_nginx
from core.system_tools import run

def get_ip_address():
    """
    Mendapatkan IP address utama yang dapat diakses di jaringan lokal (LAN).
    Menggunakan metode koneksi UDP ke server DNS Google untuk menentukan
    IP interface yang terhubung ke internet.
    
    Returns:
        str: IP address lokal, atau "127.0.0.1" jika terjadi kesalahan.
    """
    try:
        # Buat socket UDP untuk mendapatkan IP lokal yang terhubung ke internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Gunakan timeout untuk mencegah hanging
        s.settimeout(2.0)
        s.connect(("8.8.8.8", 80))  # Google DNS server
        ip = s.getsockname()[0]  # Dapatkan IP dari socket
        s.close()
        return ip
    except (socket.error, socket.timeout):
        # Tampilkan warning ke stderr
        print("[⚠] Tidak bisa mendapatkan IP eksternal, menggunakan localhost", 
              file=sys.stderr)
        return "127.0.0.1"  # Fallback ke localhost jika gagal

def run_production(env: dict, venv_python: str, project_dir: str):
    """
    Menjalankan server dalam mode produksi untuk aplikasi BMS.
    Untuk sistem Linux (kecuali Termux): Menggunakan Gunicorn + NGINX sebagai reverse proxy.
    Untuk Termux, Windows, macOS: Menggunakan Waitress saja.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                   Key yang digunakan: 'os', 'is_termux'
        venv_python (str): Path ke executable Python di dalam virtual environment
        project_dir (str): Path ke direktori root proyek
    """
    print("=== PRODUCTION MODE ===")

    # Ambil IP address server
    server_ip = get_ip_address()

    # Konfigurasi untuk Linux (bukan Termux) - gunakan Gunicorn + NGINX
    if env.get("os") == "linux" and not env.get("is_termux"):
        print(f"[✓] Server akan berjalan di:     http://{server_ip}")
        print(f"[✓] Backend (Gunicorn) di:       http://127.0.0.1:5000")
        print("[i] Menyiapkan konfigurasi NGINX...")

        try:
            # Buat dan terapkan konfigurasi NGINX
            generate_nginx_config(project_dir)
            reload_nginx()
        except Exception as e:
            print(f"[✗] Gagal mengkonfigurasi NGINX: {e}", file=sys.stderr)
            print("[i] Fallback ke Waitress tanpa NGINX...")
            # Fallback ke Waitress
            return run_waitress(venv_python, server_ip)

        # Hitung jumlah worker optimal untuk Gunicorn
        # Rumus umum: (2 * jumlah_core) + 1
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        worker_count = (2 * cpu_count) + 1
        
        # Command untuk menjalankan Gunicorn dengan konfigurasi produksi
        cmd = (
            f"{venv_python} -m gunicorn "
            f"--name bms_app "                     # Nama proses
            f"--workers {worker_count} "           # Jumlah worker optimal
            f"--worker-class gthread "            # Gunakan thread worker untuk I/O bound apps
            f"--threads 3 "                       # Thread per worker
            f"--bind 127.0.0.1:5000 "             # Binding hanya ke localhost
            f"--timeout 300 "                     # Timeout 5 menit
            f"--access-logfile - "                # Log akses ke stdout
            f"--error-logfile - "                 # Log error ke stdout
            f"--capture-output "                  # Capture output untuk logging
            f"wsgi:application"                   # Entry point aplikasi
        )

        print(f"[i] Menjalankan Gunicorn dengan {worker_count} workers...")

    else:
        # Konfigurasi untuk Termux, Windows, macOS - gunakan Waitress
        return run_waitress(venv_python, server_ip)

    # Tampilkan command yang dijalankan untuk debugging
    print(f"[cmd] {cmd}")

    # Jalankan server
    try:
        run(cmd)
    except KeyboardInterrupt:
        print("\n[i] Server dihentikan oleh pengguna")
        sys.exit(0)
    except Exception as e:
        print(f"[✗] Gagal menjalankan server: {e}", file=sys.stderr)
        sys.exit(1)

def run_waitress(venv_python: str, server_ip: str):
    """
    Menjalankan server menggunakan Waitress (untuk Windows, macOS, Termux)
    """
    print(f"[✓] Server berjalan di:          http://{server_ip}:5000")
    print("[i] Menjalankan Waitress (production).")
    
    cmd = (
        f"{venv_python} -m waitress "
        f"--listen=0.0.0.0:5000 "      # Binding ke semua interface
        f"--threads=4 "                # Default threads
        f"wsgi:application"            # Entry point aplikasi
    )
    
    print(f"[cmd] {cmd}")
    
    # Tampilkan informasi akses
    print("\n=== Production Server Aktif ===")
    print(f"Akses melalui browser: http://{server_ip}:5000")
    print("Tekan Ctrl+C untuk menghentikan server")
    print("================================\n")
    
    try:
        run(cmd)
    except KeyboardInterrupt:
        print("\n[i] Server dihentikan oleh pengguna")
        sys.exit(0)
