# core/server_prod.py

import socket
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
        s.connect(("8.8.8.8", 80))  # Google DNS server
        ip = s.getsockname()[0]  # Dapatkan IP dari socket
        s.close()
        return ip
    except:
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

        # Buat dan terapkan konfigurasi NGINX
        generate_nginx_config(project_dir)
        reload_nginx()

        # Command untuk menjalankan Gunicorn dengan konfigurasi produksi
        cmd = (
            f"{venv_python} -m gunicorn "
            f"-w 3 --threads 3 "           # 3 worker dengan 3 thread per worker
            f"-b 127.0.0.1:5000 "          # Binding hanya ke localhost (diproxy oleh NGINX)
            f"wsgi:application"            # Entry point aplikasi
        )

        print("[i] Menjalankan Gunicorn (production)...")

    else:
        # Konfigurasi untuk Termux, Windows, macOS - gunakan Waitress
        print(f"[✓] Server berjalan di:          http://{server_ip}:5000")
        print("[i] Menjalankan Waitress (fallback production).")

        # Command untuk menjalankan Waitress
        cmd = (
            f"{venv_python} -m waitress "
            f"--listen=0.0.0.0:5000 "      # Binding ke semua interface
            f"wsgi:application"            # Entry point aplikasi
        )

    # Tampilkan command yang dijalankan untuk debugging
    print(f"[cmd] {cmd}")
    
    # Jalankan server
    run(cmd)

    # Tampilkan informasi akses
    print("\n=== Production Server Aktif ===")
    print(f"Akses melalui browser: http://{server_ip}")
    print("================================\n")