from core.system_tools import run

def run_development(env: dict, venv_python: str):
    print("=== DEVELOPMENT MODE ===")

    if env.get("os") == "linux" and env.get("has_gunicorn"):
        cmd = (
            f"{venv_python} -m gunicorn "
            "-w 2 --threads 2 "
            "-b 0.0.0.0:5000 "
            "--log-level debug "
            "--capture-output "
            "--enable-stdio-inheritance "
            "wsgi:application"
        )
        print("[i] Menjalankan Gunicorn dengan real-time log.")
    else:
        cmd = (
            f"{venv_python} -m waitress "
            "--listen=0.0.0.0:5000 "
            "wsgi:application"
        )
        print("[i] Menjalankan Waitress dengan real-time log.")

    run(cmd)  # << REAL-TIME OUTPUT