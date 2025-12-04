#!/usr/bin/env python3

"""
BMS_detect.py
Deteksi OS & environment untuk BMS launcher (Mendukung Linux, Termux, Raspberry Pi, Windows, macOS)
"""

import platform
import shutil
import os
import sys


def detect():
    info = {}

    # --------------------------------------------------------------------
    # 1. DETECT SYSTEM
    # --------------------------------------------------------------------
    sys_name = platform.system().lower()
    info["os"] = sys_name               # default (linux, windows, darwin)
    info["platform"] = platform.platform()
    info["python_version"] = platform.python_version()
    info["python_executable"] = sys.executable

    # --------------------------------------------------------------------
    # 2. DETECT TERMUX (Override OS)
    # --------------------------------------------------------------------
    # Termux pasti berada di path berikut
    if os.path.exists("/data/data/com.termux/files/usr/bin"):
        info["is_termux"] = True
        info["os"] = "termux"           # override → supaya launcher tahu ini Termux
    else:
        info["is_termux"] = False

    # --------------------------------------------------------------------
    # 3. LINUX DISTRO (kecuali Termux)
    # --------------------------------------------------------------------
    distro = "unknown"
    if info["os"] == "linux" and os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    break
    info["distro"] = distro

    # --------------------------------------------------------------------
    # 4. DETECT RASPBERRY PI
    # --------------------------------------------------------------------
    is_rpi = False
    if os.path.exists("/proc/cpuinfo"):
        cpuinfo = open("/proc/cpuinfo").read().lower()
        if "bcm" in cpuinfo or "raspberry" in cpuinfo:
            is_rpi = True

    if shutil.which("vcgencmd"):
        is_rpi = True

    info["is_rpi"] = is_rpi

    # --------------------------------------------------------------------
    # 5. COMMAND AVAILABILITY
    # --------------------------------------------------------------------
    info["has_vcgencmd"] = bool(shutil.which("vcgencmd"))
    info["supports_systemd"] = bool(shutil.which("systemctl"))
    info["has_nginx"] = bool(shutil.which("nginx"))

    # Gunicorn tidak dipakai di Termux, jadi disable
    if info["os"] == "termux":
        info["has_gunicorn"] = False
    else:
        info["has_gunicorn"] = bool(shutil.which("gunicorn") or shutil.which("gunicorn3"))

    # --------------------------------------------------------------------
    # 6. RECOMMEND SERVER TYPE
    # --------------------------------------------------------------------
    if info["os"] == "linux" and not info["is_rpi"]:
        info["recommended_prod"] = "gunicorn"

    elif info["is_rpi"]:
        info["recommended_prod"] = "waitress"

    elif info["os"] == "termux":
        info["recommended_prod"] = "waitress"   # wajib di Termux

    else:
        info["recommended_prod"] = "waitress"

    # --------------------------------------------------------------------
    # 7. SUMMARY TEXT
    # --------------------------------------------------------------------
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