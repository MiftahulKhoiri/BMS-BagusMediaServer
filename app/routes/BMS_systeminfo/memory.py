import psutil
import time
from datetime import datetime

def get_memory_info():
    ram = psutil.virtual_memory()
    return {
        "total": round(ram.total / (1024**3), 2),
        "used": round(ram.used / (1024**3), 2)
    }

def get_uptime():
    boot = psutil.boot_time()
    uptime_seconds = time.time() - boot

    return {
        "hours": round(uptime_seconds / 3600, 2),
        "boot_time": datetime.fromtimestamp(boot).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }