import os
import platform
import psutil
import time
import subprocess
import json
from flask import Blueprint, jsonify, render_template
from datetime import datetime

systeminfo = Blueprint("systeminfo", __name__, url_prefix="/system")


# ======================================================
#   🔧 Helper: Ambil CPU Usage (Android Termux Safe)
# ======================================================
def get_cpu_usage_android():
    """
    Ambil CPU usage memakai Termux API.
    Jika gagal → return 0 (safe mode).
    """
    try:
        result = subprocess.run(
            ["termux-cpu-info"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return 0   # Termux API tidak ada / error

        data = json.loads(result.stdout)

        # Termux API format ada "cpu_usage": 12.3
        if "cpu_usage" in data:
            return float(data["cpu_usage"])

        return 0

    except:
        return 0  # fallback aman


# ======================================================
#   🖥 System Information (JSON)
# ======================================================
@systeminfo.route("/info")
def BMS_system_info():

    # ===== CPU via Termux API =====
    cpu_usage = get_cpu_usage_android()

    # ===== RAM =====
    ram = psutil.virtual_memory()
    ram_total = round(ram.total / (1024**3), 2)
    ram_used = round(ram.used / (1024**3), 2)

    # ===== DISK =====
    disk = psutil.disk_usage("/")
    disk_total = round(disk.total / (1024**3), 2)
    disk_used = round(disk.used / (1024**3), 2)

    # ===== SYSTEM UPTIME =====
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_hours = round(uptime_seconds / 3600, 2)
    boot_time = datetime.fromtimestamp(psutil.boot_time())

    # ===== OS & Python =====
    os_name = platform.system()
    os_version = platform.release()
    python_ver = platform.python_version()

    return jsonify({
        "cpu_usage": cpu_usage,
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