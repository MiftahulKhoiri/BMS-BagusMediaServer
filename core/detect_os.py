#!/usr/bin/env python3
"""
BMS_detect.py
Deteksi OS & environment untuk BMS
"""

import platform
import shutil
import os
import sys


def detect():
    info = {}

    # --------------------------------------------------
    # SYSTEM
    # --------------------------------------------------
    sys_name = platform.system().lower()
    info["os"] = sys_name
    info["platform"] = platform.platform()
    info["python_version"] = platform.python_version()
    info["python_executable"] = sys.executable

    # --------------------------------------------------
    # TERMUX
    # --------------------------------------------------
    if os.path.exists("/data/data/com.termux/files/usr/bin"):
        info["is_termux"] = True
        info["os"] = "termux"
    else:
        info["is_termux"] = False

    # --------------------------------------------------
    # LINUX DISTRO
    # --------------------------------------------------
    distro = "unknown"
    if info["os"] == "linux" and os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    break
    info["distro"] = distro

    # --------------------------------------------------
    # RASPBERRY PI
    # --------------------------------------------------
    is_rpi = False
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read().lower()
            if "bcm" in cpuinfo or "raspberry" in cpuinfo:
                is_rpi = True

    if shutil.which("vcgencmd"):
        is_rpi = True

    info["is_rpi"] = is_rpi

    # --------------------------------------------------
    # COMMAND AVAILABILITY
    # --------------------------------------------------
    info["has_vcgencmd"] = bool(shutil.which("vcgencmd"))
    info["supports_systemd"] = bool(shutil.which("systemctl"))
    info["has_nginx"] = bool(shutil.which("nginx"))
    info["has_gunicorn"] = False if info["os"] == "termux" else bool(
        shutil.which("gunicorn") or shutil.which("gunicorn3")
    )

    return info


def pretty_print(info):
    print("=== BMS Environment Detection ===")
    for k, v in info.items():
        print(f"{k:20}: {v}")
    print("=================================")


if __name__ == "__main__":
    pretty_print(detect())