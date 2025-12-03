#!/usr/bin/env python3

"""
BMS_detect.py
Deteksi OS & environment untuk BMS launcher
"""

import platform
import shutil
import os
import sys


def detect():
    info = {}
    sys_name = platform.system().lower()
    info["os"] = sys_name
    info["platform"] = platform.platform()
    info["python_version"] = platform.python_version()
    info["python_executable"] = sys.executable

    # distro only for Linux
    distro = "unknown"
    if sys_name == "linux" and os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    break
    info["distro"] = distro

    # detect Raspberry Pi
    is_rpi = False
    if os.path.exists("/proc/cpuinfo"):
        cpuinfo = open("/proc/cpuinfo").read().lower()
        if "bcm" in cpuinfo or "raspberry" in cpuinfo:
            is_rpi = True
    if shutil.which("vcgencmd"):
        is_rpi = True
    info["is_rpi"] = is_rpi

    # termux detection
    info["is_termux"] = os.path.exists("/data/data/com.termux")

    # commands availability
    info["has_vcgencmd"] = bool(shutil.which("vcgencmd"))
    info["supports_systemd"] = bool(shutil.which("systemctl"))
    info["has_nginx"] = bool(shutil.which("nginx"))
    info["has_gunicorn"] = bool(shutil.which("gunicorn") or shutil.which("gunicorn3"))

    # recommended
    if sys_name == "linux":
        info["recommended_prod"] = "gunicorn"
    else:
        info["recommended_prod"] = "waitress"

    info["summary"] = (
        f"OS={info['os']} | distro={info['distro']} | rpi={info['is_rpi']} | "
        f"termux={info['is_termux']} | vcgencmd={info['has_vcgencmd']} | "
        f"systemd={info['supports_systemd']}"
    )

    return info


def pretty_print(info):
    print("=== BMS Environment Detection ===")
    for k, v in info.items():
        print(f"{k:20}: {v}")
    print("=================================")


if __name__ == "__main__":
    pretty_print(detect())