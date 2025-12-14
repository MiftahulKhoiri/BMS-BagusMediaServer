# core/monitor_tools.py
import os
import socket
from core.system_tools import run

def get_ip():
    """
    Mendapatkan IP address dari sistem.
    Mencoba metode socket.gethostbyname() terlebih dahulu,
    jika mendapatkan IP loopback (127.x.x.x), mencoba menggunakan perintah hostname -I.
    
    Returns:
        str: IP address sistem atau "Unknown" jika tidak dapat ditemukan.
    """
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
    """
    Mendapatkan suhu CPU dari sistem.
    Khusus untuk Raspberry Pi dengan vcgencmd yang tersedia.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'is_rpi' dan 'has_vcgencmd'.
    
    Returns:
        str: Suhu CPU jika tersedia, "N/A" jika tidak dapat dibaca,
             atau "Not supported" jika tidak mendukung.
    """
    if env.get("is_rpi") and env.get("has_vcgencmd"):
        out = os.popen("vcgencmd measure_temp 2>/dev/null").read().strip()
        return out.replace("temp=", "") if out else "N/A"
    return "Not supported"

def get_uptime(env):
    """
    Mendapatkan waktu aktif (uptime) sistem dalam jam.
    Hanya berfungsi pada sistem Linux dengan file /proc/uptime.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    
    Returns:
        str: Uptime dalam jam dengan dua desimal,
             atau "Not supported" jika tidak mendukung.
    """
    if env.get("os") == "linux" and os.path.exists("/proc/uptime"):
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        hours = seconds / 3600
        return f"{hours:.2f} jam"
    return "Not supported"

def get_cpu_load(env):
    """
    Mendapatkan load average CPU dari sistem.
    Hanya berfungsi pada sistem Linux dengan os.getloadavg().
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    
    Returns:
        str: Load average 1, 5, dan 15 menit dalam string,
             atau "Not supported" jika tidak mendukung.
    """
    if env.get("os") == "linux":
        load1, load5, load15 = os.getloadavg()
        return f"{load1:.2f}, {load5:.2f}, {load15:.2f}"
    return "Not supported"

def get_memory_usage(env):
    """
    Mendapatkan penggunaan memori sistem.
    Hanya berfungsi pada sistem Linux dengan file /proc/meminfo.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    
    Returns:
        str: Penggunaan memori dalam format "usedMB / totalMB",
             atau "Not supported" jika tidak mendukung.
    """
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
    """
    Memeriksa status port 5000 pada localhost.
    Digunakan untuk memeriksa apakah aplikasi Flask berjalan.
    
    Returns:
        str: "Aktif" jika port terbuka, "Mati" jika tidak.
    """
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect(("127.0.0.1", 5000))
        s.close()
        return "Aktif"
    except:
        return "Mati"

def check_gunicorn(env):
    """
    Memeriksa status proses gunicorn dengan perintah pgrep.
    Hanya berfungsi pada sistem Linux.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    
    Returns:
        str: "Aktif" jika proses gunicorn ditemukan,
             "Mati" jika tidak,
             "Not available" jika tidak mendukung.
    """
    if env.get("os") != "linux":
        return "Not available"
    out = os.popen("pgrep gunicorn 2>/dev/null").read().strip()
    return "Aktif" if out else "Mati"

def check_supervisor(env):
    """
    Memeriksa status service BMS pada supervisor.
    Hanya berfungsi pada sistem Linux dengan supervisor terpasang.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
                    Diperlukan key 'os' untuk menentukan sistem operasi.
    
    Returns:
        str: "Running" jika service BMS berjalan di supervisor,
             "Stopped / Not installed" jika tidak berjalan atau tidak terpasang,
             "Not available" jika tidak mendukung.
    """
    if env.get("os") != "linux":
        return "Not available"
    out = os.popen("sudo supervisorctl status BMS 2>/dev/null").read().strip()
    if "RUNNING" in out:
        return "Running"
    return "Stopped / Not installed"

def monitoring(env):
    """
    Menampilkan informasi monitoring sistem secara keseluruhan.
    Menampilkan status OS, IP, suhu CPU, load CPU, penggunaan memori,
    uptime, status port 5000, status gunicorn, dan status supervisor.
    
    Args:
        env (dict): Dictionary environment yang berisi informasi sistem.
    """
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