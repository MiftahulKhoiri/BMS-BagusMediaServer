import os
import platform
import psutil
import time
import socket
import requests
from flask import Blueprint, jsonify, render_template
from datetime import datetime

systeminfo = Blueprint("systeminfo", __name__, url_prefix="/system")

# Try get public IP
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "Unknown"

# Try get CPU temperature
def get_cpu_temperature():
    try:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                if entry.current:
                    return entry.current
        return None
    except:
        return None

# Network speed helper
last_net = psutil.net_io_counters()
last_time = time.time()

def get_network_speed():
    global last_net, last_time
    now_net = psutil.net_io_counters()
    now_time = time.time()

    down_speed = (now_net.bytes_recv - last_net.bytes_recv) / (now_time - last_time)
    up_speed = (now_net.bytes_sent - last_net.bytes_sent) / (now_time - last_time)

    last_net = now_net
    last_time = now_time

    return round(down_speed / 1024, 2), round(up_speed / 1024, 2)


@systeminfo.route("/info")
def BMS_system_info():

    # CPU usage
    cpu = psutil.cpu_percent(interval=1)

    # Temperature
    temp = get_cpu_temperature()

    # RAM
    ram = psutil.virtual_memory()

    # Disk list
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "total": round(usage.total / 1024**3, 2),
                "used": round(usage.used / 1024**3, 2)
            })
        except:
            pass

    # Uptime
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_hours = round(uptime_seconds / 3600, 2)

    # Load avg
    try:
        load1, load5, load15 = os.getloadavg()
    except:
        load1 = load5 = load15 = 0

    # Network
    down_kb, up_kb = get_network_speed()

    # IP
    local_ip = socket.gethostbyname(socket.gethostname())
    public_ip = get_public_ip()

    # OS
    os_info = f"{platform.system()} {platform.release()}"

    return jsonify({
        "cpu": cpu,
        "temperature": temp,
        "ram_total": round(ram.total / 1024**3, 2),
        "ram_used": round(ram.used / 1024**3, 2),
        "disks": disks,
        "loadavg": {
            "1m": round(load1, 2),
            "5m": round(load5, 2),
            "15m": round(load15, 2),
        },
        "uptime_hours": uptime_hours,
        "local_ip": local_ip,
        "public_ip": public_ip,
        "net_down_kb": down_kb,
        "net_up_kb": up_kb,
        "os": os_info,
        "python": platform.python_version(),
        "boot": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    })

# ======================================================
#   🌐 GUI PAGE — BMS_systeminfo.html
# ======================================================
@systeminfo.route("/gui")
def BMS_systeminfo_gui():
    return render_template("BMS_systeminfo.html")