#!/usr/bin/env python3
"""
bms_detect.py
Deteksi OS & kemampuan environment untuk BMS launcher.
Mengembalikan dict dengan kunci: os, distro, is_rpi, supports_systemd,
has_vcgencmd, python_exec, recommended_prod_server
"""

import platform
import shutil
import os
import sys
from typing import Dict

def detect() -> Dict[str, object]:
    info = {}
    sys_name = platform.system().lower()
    info["os"] = sys_name  # 'linux', 'windows', 'darwin' (mac)
    info["platform"] = platform.platform()
    info["python_version"] = platform.python_version()
    info["python_executable"] = sys.executable

    # Detect distro (only relevant on Linux)
    distro = "unknown"
    try:
        if sys_name == "linux":
            # try reading /etc/os-release
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    data = f.read()
                for line in data.splitlines():
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split("=", 1)[1].strip().strip('"')
                        break
            else:
                distro = platform.linux_distribution()[0] if hasattr(platform, "linux_distribution") else "linux"
    except Exception:
        distro = "unknown"
    info["distro"] = distro

    # Raspberry Pi detection (simple heuristics)
    is_rpi = False
    try:
        # Common file on RPi
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as fh:
                cpuinfo = fh.read().lower()
            if "raspberry pi" in cpuinfo or "bcm" in cpuinfo:
                is_rpi = True
        # vcgencmd present (another good indicator)
        if shutil.which("vcgencmd"):
            is_rpi = True
    except Exception:
        is_rpi = is_rpi
    info["is_rpi"] = is_rpi

    # Termux detection (Android/Termux)
    is_termux = False
    if "android" in platform.system().lower() or os.getenv("ANDROID_DATA") or shutil.which("termux-info"):
        # more robust: check for /data/data/com.termux
        if os.path.exists("/data/data/com.termux"):
            is_termux = True
    info["is_termux"] = is_termux

    # vcgencmd presence
    info["has_vcgencmd"] = bool(shutil.which("vcgencmd"))

    # systemd detection (systemctl)
    info["supports_systemd"] = bool(shutil.which("systemctl"))

    # nginx presence
    info["has_nginx"] = bool(shutil.which("nginx"))

    # gunicorn presence
    info["has_gunicorn"] = False
    try:
        info["has_gunicorn"] = bool(shutil.which("gunicorn") or shutil.which("gunicorn3"))
    except Exception:
        info["has_gunicorn"] = False

    # Decide recommended production server
    # - On Linux: prefer gunicorn if available, else recommend installing gunicorn.
    # - On Windows/macOS/Termux: recommend waitress
    recommended = {}
    if sys_name == "linux":
        recommended["prod_server"] = "gunicorn" if info["has_gunicorn"] else "gunicorn (installable via pip)"
    else:
        recommended["prod_server"] = "waitress (pip install waitress)"
    info["recommended_prod"] = recommended["prod_server"]

    # Friendly summary text
    info["summary"] = (
        f"OS={info['os']} | distro={info['distro']} | rpi={info['is_rpi']} | termux={info['is_termux']} | "
        f"vcgencmd={info['has_vcgencmd']} | systemd={info['supports_systemd']}"
    )

    return info

def pretty_print(info: Dict[str, object]) -> None:
    print("=== BMS Environment Detection ===")
    for k, v in info.items():
        print(f"{k:20}: {v}")
    print("=================================")

if __name__ == "__main__":
    info = detect()
    pretty_print(info)