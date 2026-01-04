#!/usr/bin/env python3
"""
detect_os.py
Deteksi OS & environment untuk BMS dengan peningkatan akurasi dan fitur baru
"""

import platform
import shutil
import os
import sys
import subprocess
import socket
import psutil  # Tambahkan psutil untuk informasi sistem yang lebih detail
from pathlib import Path


def info_os() -> dict:
    """Mengembalikan informasi dasar sistem operasi dengan error handling"""
    info = {}
    try:
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
        info["python_implementation"] = platform.python_implementation()
        info["python_executable"] = sys.executable

    except Exception as e:
        print(f"[WARNING] Error getting OS info: {e}", file=sys.stderr)
        info["os"] = "unknown"
        info["platform"] = "unknown"

    return info


def detect_termux() -> bool:
    """Deteksi Termux dengan metode yang lebih akurat"""
    # Metode 1: Cek environment variable
    if os.environ.get('TERMUX_VERSION'):
        return True
    
    # Metode 2: Cek path khusus Termux
    termux_paths = [
        "/data/data/com.termux/files/usr/bin",
        "/data/data/com.termux/files/home",
        "/data/data/com.termux/files/usr/lib"
    ]
    
    for path in termux_paths:
        if os.path.exists(path):
            return True
    
    # Metode 3: Cek package manager Termux
    try:
        result = subprocess.run(["which", "apt"], capture_output=True, text=True)
        if "/com.termux/" in result.stdout:
            return True
    except:
        pass
    
    return False


def detect_wsl() -> bool:
    """Deteksi Windows Subsystem for Linux"""
    try:
        # Metode 1: Cek kernel version
        if "linux" in platform.system().lower():
            with open("/proc/version", "r") as f:
                content = f.read().lower()
                if "microsoft" in content or "wsl" in content:
                    return True
        
        # Metode 2: Cek uname
        result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
        if "microsoft" in result.stdout.lower():
            return True
        
        # Metode 3: Cek environment variable
        if os.environ.get('WSL_DISTRO_NAME') or os.environ.get('WSL_INTEROP'):
            return True
            
    except:
        pass
    
    return False


def detect_docker() -> bool:
    """Deteksi apakah berjalan dalam container Docker"""
    try:
        # Cek /.dockerenv file
        if os.path.exists("/.dockerenv"):
            return True
        
        # Cek cgroup
        if os.path.exists("/proc/1/cgroup"):
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if "docker" in content or "kubepods" in content:
                    return True
        
        # Cek container environment variables
        container_vars = ['KUBERNETES_SERVICE_HOST', 'CONTAINER', 'DOCKER_HOST']
        for var in container_vars:
            if os.environ.get(var):
                return True
                
    except:
        pass
    
    return False


def detect_virtual_machine() -> bool:
    """Deteksi apakah berjalan di virtual machine"""
    try:
        if platform.system().lower() == "linux":
            # Cek systemd-detect-virt
            result = subprocess.run(["systemd-detect-virt"], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "none" not in result.stdout.lower():
                return True
            
            # Cek /proc/cpuinfo untuk hypervisor
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read().lower()
                    if "hypervisor" in content:
                        return True
        
        # Cek dmesg untuk tanda-tanda virtualisasi
        try:
            result = subprocess.run(["dmesg"], capture_output=True, text=True)
            vm_indicators = ["vmware", "virtualbox", "qemu", "kvm", "hyperv"]
            for indicator in vm_indicators:
                if indicator in result.stdout.lower():
                    return True
        except:
            pass
            
    except:
        pass
    
    return False


def get_linux_distro() -> str:
    """Dapatkan informasi distro Linux dengan lebih akurat"""
    distro = "unknown"
    
    # Coba berbagai metode
    release_files = [
        "/etc/os-release",
        "/usr/lib/os-release",
        "/etc/lsb-release",
        "/etc/debian_version",
        "/etc/redhat-release",
        "/etc/centos-release",
        "/etc/fedora-release",
        "/etc/arch-release",
        "/etc/SuSE-release"
    ]
    
    for file_path in release_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    
                    if "ubuntu" in content:
                        distro = "ubuntu"
                    elif "debian" in content:
                        distro = "debian"
                    elif "centos" in content:
                        distro = "centos"
                    elif "fedora" in content:
                        distro = "fedora"
                    elif "arch" in content or "archlinux" in content:
                        distro = "arch"
                    elif "alpine" in content:
                        distro = "alpine"
                    elif "raspbian" in content:
                        distro = "raspbian"
                    elif "opensuse" in content or "suse" in content:
                        distro = "opensuse"
                    elif "mint" in content:
                        distro = "linuxmint"
                    
                    # Ambil nama lengkap dari os-release jika ada
                    if file_path == "/etc/os-release":
                        lines = content.split('\n')
                        for line in lines:
                            if line.startswith("pretty_name="):
                                distro = line.split('=', 1)[1].strip().strip('"')
                                break
                            elif line.startswith("name=") and distro == "unknown":
                                distro = line.split('=', 1)[1].strip().strip('"')
                                
                    if distro != "unknown":
                        break
                        
            except Exception as e:
                print(f"[WARNING] Error reading {file_path}: {e}", file=sys.stderr)
                continue
    
    return distro


def detect_raspberry_pi() -> bool:
    """Deteksi Raspberry Pi dengan metode yang lebih komprehensif"""
    # Metode 1: Cek /proc/device-tree/model
    if os.path.exists("/proc/device-tree/model"):
        try:
            with open("/proc/device-tree/model", "r") as f:
                content = f.read().lower()
                if "raspberry" in content:
                    return True
        except:
            pass
    
    # Metode 2: Cek /proc/cpuinfo
    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read().lower()
                if "bcm" in content or "raspberry" in content:
                    return True
        except:
            pass
    
    # Metode 3: Cek hardware dengan vcgencmd
    if shutil.which("vcgencmd"):
        return True
    
    # Metode 4: Cek /sys/firmware/devicetree/base/model
    if os.path.exists("/sys/firmware/devicetree/base/model"):
        try:
            with open("/sys/firmware/devicetree/base/model", "r") as f:
                content = f.read().lower()
                if "raspberry" in content:
                    return True
        except:
            pass
    
    return False


def get_system_memory() -> int:
    """Dapatkan total memori sistem dalam MB"""
    try:
        # Gunakan psutil jika tersedia
        if 'psutil' in sys.modules:
            mem = psutil.virtual_memory()
            return mem.total // (1024 * 1024)  # Convert to MB
        
        # Fallback untuk Linux
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_kb = int(line.split()[1])
                        return mem_kb // 1024  # Convert to MB
        
        # Fallback untuk macOS
        if platform.system().lower() == "darwin":
            result = subprocess.run(["sysctl", "hw.memsize"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                mem_bytes = int(result.stdout.split()[-1])
                return mem_bytes // (1024 * 1024)  # Convert to MB
                
    except Exception as e:
        print(f"[WARNING] Error getting memory info: {e}", file=sys.stderr)
    
    return 0


def check_command_availability() -> dict:
    """Cek ketersediaan perintah sistem yang penting"""
    commands = {
        "systemctl": "supports_systemd",
        "nginx": "has_nginx",
        "gunicorn": "has_gunicorn",
        "python3": "has_python3",
        "pip3": "has_pip3",
        "docker": "has_docker",
        "podman": "has_podman",
        "supervisorctl": "has_supervisor",
        "node": "has_node",
        "npm": "has_npm",
        "git": "has_git",
        "curl": "has_curl",
        "wget": "has_wget",
        "sudo": "has_sudo",
        "ufw": "has_ufw",  # Untuk firewall
        "fail2ban-client": "has_fail2ban",
        "certbot": "has_certbot",  # Untuk SSL
    }
    
    availability = {}
    for cmd, key in commands.items():
        availability[key] = bool(shutil.which(cmd))
    
    return availability


def detect_network_info() -> dict:
    """Deteksi informasi jaringan"""
    network_info = {}
    
    try:
        # Dapatkan hostname
        network_info["hostname"] = socket.gethostname()
        
        # Dapatkan IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        try:
            s.connect(("8.8.8.8", 80))
            network_info["local_ip"] = s.getsockname()[0]
        except:
            network_info["local_ip"] = "127.0.0.1"
        finally:
            s.close()
        
        # Cek koneksi internet
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            network_info["has_internet"] = True
        except:
            network_info["has_internet"] = False
        
        # Cek jika di belakang proxy
        network_info["http_proxy"] = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        network_info["https_proxy"] = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        
    except Exception as e:
        print(f"[WARNING] Error getting network info: {e}", file=sys.stderr)
        network_info["hostname"] = "unknown"
        network_info["local_ip"] = "127.0.0.1"
        network_info["has_internet"] = False
    
    return network_info


def detect_virtual_environment() -> dict:
    """Deteksi virtual environment Python"""
    venv_info = {}
    
    # Cek jika berjalan di virtual environment
    venv_info["in_venv"] = (hasattr(sys, 'real_prefix') or 
                           (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    
    # Path virtual environment
    if venv_info["in_venv"]:
        venv_info["venv_path"] = sys.prefix
        venv_info["venv_name"] = os.path.basename(sys.prefix)
    else:
        venv_info["venv_path"] = None
        venv_info["venv_name"] = None
    
    # Cek environment variables untuk virtual environment
    venv_info["virtual_env"] = os.environ.get('VIRTUAL_ENV')
    venv_info["conda_env"] = os.environ.get('CONDA_DEFAULT_ENV')
    
    return venv_info


def detail_os() -> dict:
    """Mengembalikan informasi detail OS dengan pengecekan lengkap"""
    # Panggil info_os() untuk data dasar
    info = info_os()
    
    # Deteksi spesifik
    info["is_termux"] = detect_termux()
    info["is_wsl"] = detect_wsl()
    info["is_docker"] = detect_docker()
    info["is_vm"] = detect_virtual_machine()
    info["is_rpi"] = detect_raspberry_pi()
    
    # Deteksi distro Linux
    if info["os"] == "linux" and not info["is_termux"]:
        info["distro"] = get_linux_distro()
    else:
        info["distro"] = "N/A"
    
    # Informasi sistem
    info["memory_mb"] = get_system_memory()
    
    # Deteksi virtual environment Python
    venv_info = detect_virtual_environment()
    info.update(venv_info)
    
    # Deteksi informasi jaringan
    network_info = detect_network_info()
    info.update(network_info)
    
    # Ketersediaan perintah
    cmd_availability = check_command_availability()
    info.update(cmd_availability)
    
    # Informasi tambahan
    info["cpu_count"] = os.cpu_count() or 1
    
    # Deteksi desktop environment (jika ada)
    info["has_gui"] = False
    if info["os"] == "linux" and not info["is_termux"]:
        # Cek jika ada DISPLAY variable
        if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            info["has_gui"] = True
        
        # Cek jika ada desktop session
        desktop = os.environ.get('XDG_CURRENT_DESKTOP') or os.environ.get('DESKTOP_SESSION')
        if desktop:
            info["desktop"] = desktop
            info["has_gui"] = True
    
    elif info["os"] == "windows" or info["os"] == "mac":
        info["has_gui"] = True
    
    # User info
    info["user"] = os.environ.get('USER') or os.environ.get('USERNAME') or "unknown"
    info["home_dir"] = os.path.expanduser("~")
    
    # Architecture detail
    info["architecture"] = platform.machine()
    info["processor"] = platform.processor() or "unknown"
    info["bits"] = platform.architecture()[0]
    
    return info


def final_os() -> str:
    """
    Mengembalikan nama OS final untuk digunakan sebagai fungsi import
    Returns:
        'linux_termux'     : Linux di Termux (Android)
        'linux_wsl'        : Linux di WSL (Windows Subsystem for Linux)
        'linux_raspberry'  : Linux di Raspberry Pi
        'linux_docker'     : Linux dalam container Docker
        'linux'            : Linux lainnya (Ubuntu, Debian, dll)
        'windows'          : Windows
        'mac'              : macOS
    """
    info = detail_os()
    
    # Prioritas deteksi
    if info.get("is_termux"):
        return "linux_termux"
    elif info.get("is_wsl"):
        return "linux_wsl"
    elif info.get("is_docker"):
        return "linux_docker"
    elif info.get("is_rpi"):
        return "linux_raspberry"
    elif info["os"] == "linux":
        return "linux"
    elif info["os"] == "windows":
        return "windows"
    elif info["os"] == "mac":
        return "mac"
    else:
        return info.get("os", "unknown")


def get_recommendations(info: dict) -> dict:
    """Berdasarkan informasi OS, berikan rekomendasi konfigurasi"""
    recommendations = {
        "server_type": "standalone",
        "wsgi_server": "waitress",
        "reverse_proxy": "none",
        "supervisor": False,
        "ssl_recommended": False,
        "optimizations": []
    }
    
    os_type = final_os()
    
    if os_type == "linux" and not info.get("is_termux"):
        recommendations["server_type"] = "production"
        recommendations["wsgi_server"] = "gunicorn"
        recommendations["reverse_proxy"] = "nginx"
        recommendations["supervisor"] = True
        recommendations["ssl_recommended"] = True
        
        if info.get("memory_mb", 0) > 4096:  # > 4GB RAM
            recommendations["optimizations"].append("high_memory")
        if info.get("cpu_count", 1) > 4:  # > 4 cores
            recommendations["optimizations"].append("multi_worker")
    
    elif os_type == "linux_raspberry":
        recommendations["server_type"] = "production"
        recommendations["wsgi_server"] = "gunicorn"
        recommendations["reverse_proxy"] = "nginx"
        recommendations["supervisor"] = True
        recommendations["ssl_recommended"] = False
        recommendations["optimizations"].append("low_resource")
    
    elif os_type in ["linux_termux", "linux_wsl"]:
        recommendations["server_type"] = "development"
        recommendations["wsgi_server"] = "waitress"
        recommendations["reverse_proxy"] = "none"
        recommendations["supervisor"] = False
        recommendations["optimizations"].append("development_env")
    
    elif os_type in ["windows", "mac"]:
        recommendations["server_type"] = "development"
        recommendations["wsgi_server"] = "waitress"
        recommendations["reverse_proxy"] = "none"
        recommendations["supervisor"] = False
        
        if info.get("has_gui"):
            recommendations["optimizations"].append("gui_env")
    
    # Tambahan rekomendasi berdasarkan spesifikasi
    if info.get("has_internet") and not info.get("http_proxy"):
        recommendations["optimizations"].append("direct_internet")
    
    if info.get("in_venv"):
        recommendations["optimizations"].append("virtual_env")
    
    return recommendations


def pretty_print(info: dict):
    """Mencetak informasi dengan format rapi dan berwarna"""
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
    except ImportError:
        # Fallback jika colorama tidak tersedia
        class SimpleColors:
            RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET_ALL = ""
        Fore = SimpleColors()
        Style = SimpleColors()
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}BMS Environment Detection")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # Kelompokkan output
    categories = {
        "📊 Sistem Dasar": [
            ("OS", "os"),
            ("Platform", "platform"),
            ("Distro", "distro"),
            ("Arsitektur", "architecture"),
            ("Processor", "processor"),
            ("Bit", "bits")
        ],
        "🐍 Python": [
            ("Versi Python", "python_version"),
            ("Implementasi", "python_implementation"),
            ("Executable", "python_executable"),
            ("Virtual Env", "venv_name"),
            ("Di Virtual Env", "in_venv")
        ],
        "🔍 Deteksi Spesifik": [
            ("Termux", "is_termux"),
            ("WSL", "is_wsl"),
            ("Docker", "is_docker"),
            ("Virtual Machine", "is_vm"),
            ("Raspberry Pi", "is_rpi"),
            ("GUI Available", "has_gui")
        ],
        "💾 Hardware": [
            ("CPU Cores", "cpu_count"),
            ("Memory (MB)", "memory_mb")
        ],
        "🌐 Jaringan": [
            ("Hostname", "hostname"),
            ("Local IP", "local_ip"),
            ("Internet", "has_internet")
        ],
        "🛠️ Tools Available": [
            ("Systemd", "supports_systemd"),
            ("Nginx", "has_nginx"),
            ("Gunicorn", "has_gunicorn"),
            ("Docker", "has_docker"),
            ("Supervisor", "has_supervisor"),
            ("Node.js", "has_node"),
            ("Git", "has_git"),
            ("Sudo", "has_sudo")
        ]
    }
    
    for category, items in categories.items():
        print(f"\n{Fore.GREEN}{category}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'-'*40}")
        
        for display_name, key in items:
            if key in info:
                value = info[key]
                
                # Format nilai boolean
                if isinstance(value, bool):
                    color = Fore.GREEN if value else Fore.RED
                    display_value = f"{color}{'✓ Ya' if value else '✗ Tidak'}{Style.RESET_ALL}"
                elif value is None:
                    display_value = f"{Fore.YELLOW}Tidak tersedia{Style.RESET_ALL}"
                else:
                    display_value = f"{Fore.CYAN}{value}{Style.RESET_ALL}"
                
                print(f"  {display_name:20}: {display_value}")
    
    # Tampilkan rekomendasi
    recommendations = get_recommendations(info)
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}💡 Rekomendasi:{Style.RESET_ALL}")
    print(f"  Server Type: {recommendations['server_type']}")
    print(f"  WSGI Server: {recommendations['wsgi_server']}")
    print(f"  Reverse Proxy: {recommendations['reverse_proxy']}")
    print(f"  Supervisor: {'Disarankan' if recommendations['supervisor'] else 'Tidak perlu'}")
    print(f"  SSL: {'Disarankan' if recommendations['ssl_recommended'] else 'Opsional'}")
    
    if recommendations['optimizations']:
        print(f"  Optimasi: {', '.join(recommendations['optimizations'])}")
    
    # Tampilkan OS final
    final_type = final_os()
    os_display_names = {
        "linux_termux": "Linux (Termux/Android)",
        "linux_wsl": "Linux (WSL/Windows)",
        "linux_docker": "Linux (Docker Container)",
        "linux_raspberry": "Linux (Raspberry Pi)",
        "linux": "Linux",
        "windows": "Windows",
        "mac": "macOS"
    }
    
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}✅ Tipe OS terdeteksi: {os_display_names.get(final_type, final_type)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def export_as_env() -> str:
    """Ekspor informasi OS sebagai environment variables string"""
    info = detail_os()
    env_lines = ["# BMS Environment Variables"]
    
    for key, value in info.items():
        if isinstance(value, bool):
            value_str = "1" if value else "0"
        elif isinstance(value, (int, float)):
            value_str = str(value)
        elif value is None:
            value_str = ""
        else:
            value_str = str(value)
        
        env_lines.append(f"export BMS_{key.upper()}=\"{value_str}\"")
    
    return "\n".join(env_lines)


if __name__ == "__main__":
    try:
        # Coba import psutil, jika tidak ada, beri warning
        try:
            import psutil
        except ImportError:
            print("[INFO] psutil tidak tersedia. Beberapa fitur mungkin terbatas.")
            print("[INFO] Install dengan: pip install psutil")
        
        info = detail_os()
        pretty_print(info)
        
        # Opsi untuk mengekspor sebagai env
        if len(sys.argv) > 1 and sys.argv[1] == "--export-env":
            print(export_as_env())
        
        # Opsi untuk mendapatkan tipe OS saja
        elif len(sys.argv) > 1 and sys.argv[1] == "--simple":
            print(final_os())
        
    except Exception as e:
        print(f"[ERROR] Failed to detect OS: {e}", file=sys.stderr)
        sys.exit(1)