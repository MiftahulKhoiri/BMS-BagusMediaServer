import os
import platform
from flask import jsonify, render_template

from . import systeminfo
from .cpu import get_cpu_usage
from .disk import safe_disk_usage
from .memory import get_memory_info, get_uptime


@systeminfo.route("/info")
def BMS_system_info():
    try:
        cpu_usage = get_cpu_usage()
        ram = get_memory_info()
        uptime = get_uptime()
        disk_total, disk_used = safe_disk_usage()

        load_avg = None
        if hasattr(os, "getloadavg"):
            try:
                la = os.getloadavg()
                load_avg = {
                    "1m": la[0],
                    "5m": la[1],
                    "15m": la[2]
                }
            except:
                pass

        return jsonify({
            "cpu_usage": cpu_usage,
            "ram_total": ram["total"],
            "ram_used": ram["used"],
            "disk_total": disk_total,
            "disk_used": disk_used,
            "uptime_hours": uptime["hours"],
            "boot_time": uptime["boot_time"],
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "load_average": load_avg
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@systeminfo.route("/gui")
def BMS_systeminfo_gui():
    return render_template("BMS_systeminfo.html")