import subprocess
import json
import psutil

def get_cpu_usage():
    """
    Termux API → fallback psutil
    Aman semua platform
    """
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

    try:
        return psutil.cpu_percent(interval=0.5)
    except:
        return 0.0