import os
import platform
import psutil
import time
from flask import Blueprint, jsonify, render_template
from datetime import datetime

systeminfo = Blueprint("systeminfo", __name__, url_prefix="/system")


# ======================================================
#   🖥 System Information (JSON)
# ======================================================
@systeminfo.route("/info")
def BMS_system_info():

    # CPU usage
    cpu = psutil.cpu_percent(interval=1)

    # RAM usage
    ram = psutil.virtual_memory()
    ram_total = round(ram.total / (1024**3), 2)
    ram_used = round(ram.used / (1024**3), 2)

    # Disk usage
    disk = psutil.disk_usage("/")
    disk_total = round(disk.total / (1024**3), 2)
    disk_used = round(disk.used / (1024**3), 2)

    # System uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_hours = round(uptime_seconds / 3600, 2)

    # OS info
    os_name = platform.system()
    os_version = platform.release()

    # Python version
    python_ver = platform.python_version()

    return jsonify({
        "cpu_usage": cpu,
        "ram_total": ram_total,
        "ram_used": ram_used,
        "disk_total": disk_total,
        "disk_used": disk_used,
        "uptime_hours": uptime_hours,
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "os": f"{os_name} {os_version}",
        "python": python_ver
    })


# ======================================================
#   🌐 GUI PAGE — BMS_systeminfo.html
# ======================================================
@systeminfo.route("/gui")
def BMS_systeminfo_gui():
    return render_template("BMS_systeminfo.html")