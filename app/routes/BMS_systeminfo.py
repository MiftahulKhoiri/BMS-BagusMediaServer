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
#  Helper: CPU Usage (Termux Safe + Cross-platform)
# ======================================================
def get_cpu_usage():
    """
    Jika Termux API tersedia → gunakan termux-cpu-info.
    Jika tidak → gunakan psutil.cpu_percent().
    Aman untuk semua platform.
    """
    # Coba Termux API dulu
    try:
        result = subprocess.run(
            ["termux-cpu-info"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "cpu_usage" in data:
                return float(data["cpu_usage"])
    except:
        pass

    # Fallback universal
    try:
        return psutil.cpu_percent(interval=0.5)
    except:
        return 0.0


# ======================================================
#  Helper: Disk Safe for Linux / Termux / Windows
# ======================================================
def safe_disk_usage():
    try:
        # Windows pakai drive C:
        if platform.system().lower() == "windows":
            root = os.getenv("SystemDrive", "C:\\")
        else:
            root = "/"

        d = psutil.disk_usage(root)
        return round(d.total / (1024**3), 2), round(d.used / (1024**3), 2)
    except:
        return 0, 0


# ======================================================
#  SYSTEM INFORMATION (JSON)
# ======================================================
@systeminfo.route("/info")
def BMS_system_info():

    try:
        cpu_usage = get_cpu_usage()

        # RAM
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024**3), 2)
        ram_used = round(ram.used / (1024**3), 2)

        # Disk
        disk_total, disk_used = safe_disk_usage()

        # Uptime
        boot = psutil.boot_time()
        uptime_seconds = time.time() - boot
        uptime_hours = round(uptime_seconds / 3600, 2)
        boot_time = datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")

        # Load average (Linux only)
        load_avg = None
        if hasattr(os, "getloadavg"):
            try:
                la = os.getloadavg()
                load_avg = {"1m": la[0], "5m": la[1], "15m": la[2]}
            except:
                load_avg = None

        return jsonify({
            "cpu_usage": cpu_usage,
            "ram_total": ram_total,
            "ram_used": ram_used,
            "disk_total": disk_total,
            "disk_used": disk_used,
            "uptime_hours": uptime_hours,
            "boot_time": boot_time,
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "load_average": load_avg
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
#  GUI PAGE
# ======================================================
@systeminfo.route("/gui")
def BMS_systeminfo_gui():
    return render_template("BMS_systeminfo.html")