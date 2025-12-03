# core/monitor_tools.py
import os
import socket
from core.system_tools import run

def get_ip():
    try:
        # Try gethostbyname first; fallback to hostname -I
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127."):
            out = os.popen("hostname -I 2>/dev/null").read().strip()
            if out:
                ip = out.split()[0]
        return ip
    except:
        return "Unknown"

def get_cpu_temp(env):
    if env.get("is_rpi") and env.get("has_vcgencmd"):
        out = os.popen("vcgencmd measure_temp 2>/dev/null").read().strip()
        return out.replace("temp=", "") if out else "N/A"
    return "Not supported"

def get_uptime(env):
    if env.get("os") == "linux" and os.path.exists("/proc/uptime"):
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        hours = seconds / 3600
        return f"{hours:.2f} jam"
    return "Not supported"

def get_cpu_load(env):
    if env.get("os") == "linux":
        load1, load5, load15 = os.getloadavg()
        return f"{load1:.2f}, {load5:.2f}, {load15:.2f}"
    return "Not supported"

def get_memory_usage(env):
    if env.get("os") == "linux" and os.path.exists("/proc/meminfo"):
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, val = line.split(":", 1)
                meminfo[key.strip()] = int(val.strip().split()[0])
        total = meminfo.get("MemTotal", 0) // 1024
        avail = meminfo.get("MemAvailable", 0) // 1024
        used = total - avail
        return f"{used}MB / {total}MB"
    return "Not supported"

def check_port_5000():
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect(("127.0.0.1", 5000))
        s.close()
        return "Aktif"
    except:
        return "Mati"

def check_gunicorn(env):
    if env.get("os") != "linux":
        return "Not available"
    out = os.popen("pgrep gunicorn 2>/dev/null").read().strip()
    return "Aktif" if out else "Mati"

def check_supervisor(env):
    if env.get("os") != "linux":
        return "Not available"
    out = os.popen("sudo supervisorctl status BMS 2>/dev/null").read().strip()
    if "RUNNING" in out:
        return "Running"
    return "Stopped / Not installed"

def monitoring(env):
    print("====== BMS SYSTEM MONITORING ======")
    print(f"OS                 : {env.get('os')}")
    print(f"IP Address         : {get_ip()}")
    print(f"CPU Temperature    : {get_cpu_temp(env)}")
    print(f"CPU Load (1/5/15)  : {get_cpu_load(env)}")
    print(f"Memory Usage       : {get_memory_usage(env)}")
    print(f"Uptime             : {get_uptime(env)}")
    print("-----------------------------------")
    print(f"Port 5000 Status   : {check_port_5000()}")
    print(f"Gunicorn Status    : {check_gunicorn(env)}")
    print(f"Supervisor Status  : {check_supervisor(env)}")
    print("===================================")