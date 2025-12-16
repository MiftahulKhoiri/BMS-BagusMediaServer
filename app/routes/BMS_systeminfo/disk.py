import os
import platform
import psutil

def safe_disk_usage():
    try:
        if platform.system().lower() == "windows":
            root = os.getenv("SystemDrive", "C:\\")
        else:
            root = "/"

        d = psutil.disk_usage(root)
        return round(d.total / (1024**3), 2), round(d.used / (1024**3), 2)
    except:
        return 0, 0