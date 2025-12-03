import os
import signal
from flask import Blueprint, jsonify

BMS_power = Blueprint("BMS_power", __name__)


# -------------------------------
# 1. SHUTDOWN SERVER
# -------------------------------
@BMS_power.route("/server/shutdown", methods=["POST"])
def shutdown_server():

    # Jika Gunicorn daemon
    pid_file = "/tmp/gunicorn.pid"

    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)

    # Hentikan Nginx juga
    os.system("sudo systemctl stop nginx")

    return jsonify({
        "status": "success",
        "message": "Server dimatikan."
    })
    

# -------------------------------
# 2. RESTART SERVER
# -------------------------------
@BMS_power.route("/server/restart", methods=["POST"])
def restart_server():

    # Matikan Gunicorn
    pid_file = "/tmp/gunicorn.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)

    # Mulai ulang Gunicorn daemon
    os.system(
        "gunicorn -w 3 --threads 2 -b 127.0.0.1:5000 "
        "--daemon --pid /tmp/gunicorn.pid "
        "--access-logfile /tmp/gunicorn_access.log "
        "--error-logfile /tmp/gunicorn_error.log "
        "app:create_app()"
    )

    return jsonify({
        "status": "success",
        "message": "Server berhasil direstart."
    })