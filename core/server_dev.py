from core.system_tools import run

def run_development(env: dict, venv_python: str):
    """
    Menjalankan server development untuk aplikasi BMS.
    Memilih antara Gunicorn (untuk Linux dengan gunicorn terpasang) atau Waitress (untuk platform lain)
    dengan output real-time untuk keperluan debugging.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Key yang digunakan: 'os' dan 'has_gunicorn'
        venv_python (str): Path ke executable Python di dalam virtual environment
    """
    print("=== DEVELOPMENT MODE ===")

    # Gunakan Gunicorn jika di Linux dan gunicorn tersedia
    if env.get("os") == "linux" and env.get("has_gunicorn"):
        cmd = (
            f"{venv_python} -m gunicorn "
            "-w 2 --threads 2 "                    # 2 worker dengan 2 thread per worker
            "-b 0.0.0.0:5000 "                     # Binding ke semua interface pada port 5000
            "--log-level debug "                   # Level log debug untuk output detail
            "--capture-output "                    # Capture output untuk logging
            "--enable-stdio-inheritance "          # Warisi stdio untuk real-time output
            "wsgi:application"                     # Entry point aplikasi
        )
        print("[i] Menjalankan Gunicorn dengan real-time log.")
    else:
        # Fallback ke Waitress untuk platform non-Linux atau tanpa gunicorn
        cmd = (
            f"{venv_python} -m waitress "
            "--listen=0.0.0.0:5000 "              # Binding ke semua interface pada port 5000
            "wsgi:application"                    # Entry point aplikasi
        )
        print("[i] Menjalankan Waitress dengan real-time log.")

    # Jalankan command dengan output real-time
    run(cmd)  # << REAL-TIME OUTPUT