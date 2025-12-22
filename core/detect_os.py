#!/usr/bin/env python3
"""
detect_os.py
Deteksi OS & environment untuk BMS
"""

import platform
import shutil
import os
import sys


def info_os():
    """Mengembalikan informasi dasar sistem operasi"""
    info = {}
    sys_name = platform.system().lower()
    
    # Identifikasi OS dasar
    if sys_name == "linux":
        info["os"] = "linux"
    elif sys_name == "darwin":
        info["os"] = "mac"
    elif sys_name == "windows":
        info["os"] = "windows"
    else:
        info["os"] = sys_name  # untuk OS lain yang jarang
    
    # Informasi tambahan
    info["platform"] = platform.platform()
    info["python_version"] = platform.python_version()
    info["python_executable"] = sys.executable
    
    return info


def detail_os():
    """Mengembalikan informasi detail OS dengan pengecekan lengkap"""
    # Panggil info_os() untuk data dasar
    info = info_os()
    
    # --------------------------------------------------
    # DETEKSI TERMUX (Android)
    # --------------------------------------------------
    if info["os"] == "linux" and os.path.exists("/data/data/com.termux/files/usr/bin"):
        info["is_termux"] = True
        info["os_detail"] = "termux"
    else:
        info["is_termux"] = False
    
    # --------------------------------------------------
    # DETEKSI DISTRO LINUX
    # --------------------------------------------------
    info["distro"] = "unknown"
    if info["os"] == "linux" and not info.get("is_termux", False):
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", encoding='utf-8') as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        info["distro"] = line.split("=", 1)[1].strip().strip('"')
                        break
        elif os.path.exists("/etc/lsb-release"):
            with open("/etc/lsb-release", encoding='utf-8') as f:
                for line in f:
                    if line.startswith("DISTRIB_DESCRIPTION="):
                        info["distro"] = line.split("=", 1)[1].strip().strip('"')
                        break
    
    # --------------------------------------------------
    # DETEKSI RASPBERRY PI
    # --------------------------------------------------
    info["is_rpi"] = False
    if info["os"] == "linux":
        # Metode 1: Cek di /proc/cpuinfo
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", encoding='utf-8') as f:
                cpuinfo = f.read().lower()
                if "bcm" in cpuinfo or "raspberry" in cpuinfo:
                    info["is_rpi"] = True
        
        # Metode 2: Cek ketersediaan vcgencmd
        if shutil.which("vcgencmd"):
            info["is_rpi"] = True
    
    # --------------------------------------------------
    # DETEKSI WINDOWS DETAIL
    # --------------------------------------------------
    if info["os"] == "windows":
        # Cek versi Windows
        win_version = platform.version()
        info["windows_version"] = win_version
        
        # Cek apakah Windows 10/11
        if "10.0.22000" in win_version or "10.0.22621" in win_version:
            info["windows_edition"] = "Windows 11"
        elif "10.0" in win_version:
            info["windows_edition"] = "Windows 10"
        elif "6.3" in win_version:
            info["windows_edition"] = "Windows 8.1"
        elif "6.2" in win_version:
            info["windows_edition"] = "Windows 8"
        elif "6.1" in win_version:
            info["windows_edition"] = "Windows 7"
        else:
            info["windows_edition"] = "Windows"
    
    # --------------------------------------------------
    # DETEKSI MAC DETAIL
    # --------------------------------------------------
    elif info["os"] == "mac":
        # Versi macOS
        mac_version = platform.mac_ver()[0]
        info["mac_version"] = mac_version
        
        # Coba tentukan nama macOS
        if mac_version.startswith("13."):
            info["mac_edition"] = "Ventura"
        elif mac_version.startswith("12."):
            info["mac_edition"] = "Monterey"
        elif mac_version.startswith("11."):
            info["mac_edition"] = "Big Sur"
        elif mac_version.startswith("10.15"):
            info["mac_edition"] = "Catalina"
        elif mac_version.startswith("10.14"):
            info["mac_edition"] = "Mojave"
        else:
            info["mac_edition"] = "macOS"
    
    # --------------------------------------------------
    # KETERSEDIAAN PERINTAH SISTEM
    # --------------------------------------------------
    info["has_vcgencmd"] = bool(shutil.which("vcgencmd"))
    info["supports_systemd"] = bool(shutil.which("systemctl"))
    info["has_nginx"] = bool(shutil.which("nginx"))
    
    # Untuk gunicorn, skip jika di Termux
    if info.get("is_termux", False):
        info["has_gunicorn"] = False
    else:
        info["has_gunicorn"] = bool(shutil.which("gunicorn") or shutil.which("gunicorn3"))
    
    # Cek architektur
    info["architecture"] = platform.machine()
    info["processor"] = platform.processor()
    
    # RAM info (perkiraan)
    if info["os"] == "linux":
        try:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_kb = int(line.split()[1])
                            info["ram_mb"] = mem_kb // 1024
                            break
        except:
            info["ram_mb"] = "unknown"
    else:
        info["ram_mb"] = "unknown"
    
    return info


def final_os():
    """
    Mengembalikan nama OS final untuk digunakan sebagai fungsi import
    Returns:
        'linux_termux'     : Linux di Termux (Android)
        'linux_raspberry'  : Linux di Raspberry Pi
        'linux'            : Linux lainnya (Ubuntu, Debian, dll)
        'windows'          : Windows
        'mac'              : macOS
    """
    # Dapatkan informasi detail OS
    info = detail_os()
    
    # Deteksi Termux (Android)
    if info.get("is_termux"):
        return "linux_termux"
    
    # Deteksi Raspberry Pi
    elif info.get("is_rpi"):
        return "linux_raspberry"
    
    # Deteksi OS lainnya
    elif info["os"] == "linux":
        return "linux"
    
    elif info["os"] == "windows":
        return "windows"
    
    elif info["os"] == "mac":
        return "mac"
    
    else:
        # Fallback untuk OS yang tidak dikenali
        return info["os"]


def pretty_print(info):
    """Mencetak informasi dengan format rapi"""
    print("\n" + "="*50)
    print("BMS Environment Detection")
    print("="*50)
    
    # Kelompokkan output
    categories = {
        "Sistem Dasar": ["os", "platform", "architecture", "processor"],
        "Python": ["python_version", "python_executable"],
        "Detail OS": ["os_detail", "distro", "windows_edition", "mac_edition", "windows_version", "mac_version"],
        "Device Specific": ["is_termux", "is_rpi"],
        "Available Commands": ["has_vcgencmd", "supports_systemd", "has_nginx", "has_gunicorn"],
        "Hardware": ["ram_mb"]
    }
    
    for category, keys in categories.items():
        print(f"\n[{category}]")
        for key in keys:
            if key in info:
                value = info[key]
                if isinstance(value, bool):
                    value = "Ya" if value else "Tidak"
                print(f"  {key:20}: {value}")
    
    print("\n" + "="*50)

