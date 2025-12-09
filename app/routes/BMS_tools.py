import os
import signal
import subprocess
import json
from flask import Blueprint, request, jsonify, session, current_app

from app.routes.BMS_logger import BMS_write_log
from app.routes.BMS_auth import BMS_auth_is_root

tools = Blueprint("tools", __name__, url_prefix="/tools")

# log file lokal fallback (tidak wajib)
LOG_FILE = os.path.join(os.getcwd(), "bms_tools.log")


# -----------------------------
# Utilities
# -----------------------------
def _write_local_log(msg: str):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _run_cmd_list(cmd_list, timeout=15):
    """
    Jalankan perintah sebagai list (tanpa shell) dan kembalikan (ok_bool, stdout+stderr)
    """
    try:
        p = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        out = p.stdout or ""
        return p.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


# -----------------------------
# Helpers untuk deteksi project / venv / gunicorn
# -----------------------------
def detect_project_dir():
    base = os.path.dirname(os.path.abspath(__file__))  # .../app/routes
    project = os.path.abspath(os.path.join(base, "..", ".."))
    return project


def detect_venv_python(project_dir):
    # cek beberapa nama virtualenv umum (.venv, venv, env)
    candidates = [
        os.path.join(project_dir, ".venv", "bin", "python"),
        os.path.join(project_dir, ".venv", "bin", "python3"),
        os.path.join(project_dir, "venv", "bin", "python"),
        os.path.join(project_dir, "venv", "bin", "python3"),
        os.path.join(project_dir, "env", "bin", "python"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def detect_gunicorn_bin(project_dir):
    candidates = [
        os.path.join(project_dir, ".venv", "bin", "gunicorn"),
        os.path.join(project_dir, "venv", "bin", "gunicorn"),
        "/usr/bin/gunicorn",
        "/usr/local/bin/gunicorn"
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def detect_wsgi(project_dir):
    wsgi_file = os.path.join(project_dir, "wsgi.py")
    if os.path.exists(wsgi_file):
        # fallback: assume wsgi exposes "application"
        return "wsgi:application"
    # default: app:create_app()
    return "app:create_app()"


# -----------------------------
# Process control (safe)
# -----------------------------
def stop_gunicorn():
    pid_file = "/tmp/gunicorn.pid"
    if not os.path.exists(pid_file):
        return False, "Gunicorn pid file tidak ditemukan."

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        return True, f"Gunicorn (PID {pid}) dihentikan."
    except Exception as e:
        return False, f"Gagal hentikan Gunicorn: {e}"


def start_gunicorn(venv_python, wsgi_target, project_dir):
    # jalankan gunicorn menggunakan modul -m, tanpa shell
    cmd = [venv_python, "-m", "gunicorn", "-w", "3", "--threads", "3", "-b", "127.0.0.1:5000",
           "--daemon", "--pid", "/tmp/gunicorn.pid",
           "--access-logfile", "/tmp/gunicorn_access.log",
           "--error-logfile", "/tmp/gunicorn_error.log",
           wsgi_target]
    return _run_cmd_list(cmd)


def stop_nginx():
    # tidak pakai sudo otomatis; coba systemctl stop nginx jika tersedia
    rc, out = _run_cmd_list(["systemctl", "stop", "nginx"])
    if rc:
        return True, "NGINX diberhentikan lewat systemctl."
    # fallback: coba service stop nginx
    rc2, out2 = _run_cmd_list(["service", "nginx", "stop"])
    if rc2:
        return True, "NGINX diberhentikan lewat service."
    return False, f"Gagal hentikan NGINX: {out} {out2}"


def start_nginx():
    rc, out = _run_cmd_list(["systemctl", "start", "nginx"])
    if rc:
        return True, "NGINX dimulai lewat systemctl."
    rc2, out2 = _run_cmd_list(["service", "nginx", "start"])
    if rc2:
        return True, "NGINX dimulai lewat service."
    return False, f"Gagal start NGINX: {out} {out2}"


def stop_flask_dev_from_env(request_env):
    # Hanya berlaku jika ada werkzeug shutdown function
    func = request_env.get("werkzeug.server.shutdown")
    if callable(func):
        try:
            func()
            return True, "Flask dev server dihentikan via werkzeug."
        except Exception as e:
            return False, f"Gagal hentikan Flask dev: {e}"
    return False, "Flask dev shutdown function tidak tersedia."


# -----------------------------
# ROUTES (HANYA ROOT)
# -----------------------------
def _require_root():
    if not session.get("user_id"):
        return jsonify({"error": "Belum login"}), 403
    if session.get("role") != "root":
        return jsonify({"error": "Perlu role root"}), 403
    return None


@tools.route("/info")
def tools_info():
    """
    Informasi deteksi environment (project dir, venv, gunicorn)
    GET /tools/info
    """
    req = _require_root()
    if req:
        return req

    PROJECT_DIR = detect_project_dir()
    return jsonify({
        "project": PROJECT_DIR,
        "venv_python": detect_venv_python(PROJECT_DIR),
        "gunicorn_bin": detect_gunicorn_bin(PROJECT_DIR),
        "wsgi_target": detect_wsgi(PROJECT_DIR)
    })


@tools.route("/restart", methods=["POST"])
def BMS_tools_restart():
    """
    Restart sequence:
    1) stop gunicorn (if pid found)
    2) stop nginx (if available)
    3) start nginx (if available)
    4) start gunicorn via venv python -m gunicorn
    """
    req = _require_root()
    if req:
        return req

    PROJECT_DIR = detect_project_dir()
    VENV_PY = detect_venv_python(PROJECT_DIR)
    GUNICORN_BIN = detect_gunicorn_bin(PROJECT_DIR)
    WSGI_TARGET = detect_wsgi(PROJECT_DIR)

    detail = {
        "project": PROJECT_DIR,
        "venv_python": VENV_PY,
        "gunicorn_bin": GUNICORN_BIN,
        "wsgi_target": WSGI_TARGET,
        "actions": {}
    }

    # Validate
    if not VENV_PY:
        detail["error"] = "Virtualenv python tidak ditemukan. Pastikan virtualenv ada (.venv / venv)."
        return jsonify(detail), 400

    # stop gunicorn
    ok, msg = stop_gunicorn()
    detail["actions"]["stop_gunicorn"] = msg

    # stop nginx
    ok_ng, msg_ng = stop_nginx()
    detail["actions"]["stop_nginx"] = msg_ng

    # stop flask dev (best-effort)
    ok_fl, msg_fl = stop_flask_dev_from_env(request.environ)
    detail["actions"]["stop_flask_dev"] = msg_fl

    # start nginx (best-effort)
    ok_sng, msg_sng = start_nginx()
    detail["actions"]["start_nginx"] = msg_sng

    # start gunicorn
    ok_gs, out_gs = start_gunicorn(VENV_PY, WSGI_TARGET, PROJECT_DIR)
    detail["actions"]["start_gunicorn"] = out_gs if ok_gs else f"Failed: {out_gs}"

    # Log
    BMS_write_log("TOOLS: restart requested", session.get("username", "UNKNOWN"))
    _write_local_log(json.dumps(detail))

    return jsonify({"status": "restart_done", "detail": detail})


@tools.route("/shutdown", methods=["POST"])
def BMS_tools_shutdown():
    """
    Shutdown sequence: stop gunicorn/nginx/flask dev if possible.
    """
    req = _require_root()
    if req:
        return req

    detail = {}

    ok_g, msg_g = stop_gunicorn()
    detail["stop_gunicorn"] = msg_g

    ok_ng, msg_ng = stop_nginx()
    detail["stop_nginx"] = msg_ng

    ok_fl, msg_fl = stop_flask_dev_from_env(request.environ)
    detail["stop_flask_dev"] = msg_fl

    BMS_write_log("TOOLS: shutdown requested", session.get("username", "UNKNOWN"))
    _write_local_log(json.dumps(detail))

    return jsonify({"status": "shutdown_done", "detail": detail})


@tools.route("/log")
def BMS_tools_get_log():
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({"log": ""})
        with open(LOG_FILE, "r") as f:
            content = f.read()
        return jsonify({"log": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tools.route("/log/clear", methods=["POST"])
def BMS_tools_clear_log():
    req = _require_root()
    if req:
        return req
    try:
        open(LOG_FILE, "w").close()
        BMS_write_log("TOOLS: log cleared", session.get("username", "UNKNOWN"))
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500