# core/monitor_tools.py
import os
import sys
import socket
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
from core.system_tools import run, is_command_available


def get_ip() -> dict:
    """
    Mendapatkan semua IP address dari sistem.
    
    Returns:
        dict: Dictionary dengan berbagai jenis IP address
    """
    ips = {
        "local_ip": "127.0.0.1",
        "public_ip": None,
        "all_ips": [],
        "interfaces": {}
    }
    
    try:
        # Metode 1: Socket connection untuk mendapatkan IP utama
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        try:
            s.connect(("8.8.8.8", 80))
            ips["local_ip"] = s.getsockname()[0]
        except:
            pass
        finally:
            s.close()
        
        # Metode 2: Mengumpulkan semua IP dari interfaces
        if sys.platform == "win32":
            # Windows
            try:
                import netifaces
                for iface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr.get('addr')
                            if ip and ip != '127.0.0.1':
                                ips["all_ips"].append(ip)
                                ips["interfaces"][iface] = ip
            except ImportError:
                # Fallback untuk Windows tanpa netifaces
                result = run("ipconfig | findstr /i \"ipv4\"")
                if result and result.stdout:
                    for line in result.stdout.split('\n'):
                        if 'IPv4' in line:
                            ip = line.split(':')[-1].strip()
                            if ip and ip != '127.0.0.1':
                                ips["all_ips"].append(ip)
        
        elif sys.platform == "linux" or sys.platform == "darwin":
            # Linux/macOS
            if is_command_available("hostname"):
                result = run("hostname -I 2>/dev/null || true")
                if result and result.stdout:
                    for ip in result.stdout.strip().split():
                        if ip and ip != '127.0.0.1':
                            ips["all_ips"].append(ip)
            
            if is_command_available("ip"):
                result = run("ip -4 -o addr show 2>/dev/null | awk '{print $2 \": \" $4}' || true")
                if result and result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            iface, ip_with_mask = line.split(':', 1)
                            ip = ip_with_mask.split('/')[0].strip()
                            if ip and ip != '127.0.0.1':
                                ips["interfaces"][iface.strip()] = ip
        
        # Coba dapatkan public IP (jika ada koneksi internet)
        try:
            import urllib.request
            with urllib.request.urlopen("https://api.ipify.org", timeout=3) as response:
                ips["public_ip"] = response.read().decode('utf-8').strip()
        except:
            pass
        
        # Jika tidak ada IP selain localhost, coba socket.gethostbyname
        if not ips["all_ips"] and not any(v for k, v in ips.items() if k != "local_ip" and v):
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                if not ip.startswith("127."):
                    ips["all_ips"].append(ip)
            except:
                pass
    
    except Exception as e:
        print(f"[WARNING] Error getting IPs: {e}", file=sys.stderr)
    
    return ips


def get_cpu_temp(env: dict) -> dict:
    """
    Mendapatkan suhu CPU dari berbagai platform.
    
    Args:
        env (dict): Environment dictionary
        
    Returns:
        dict: Informasi suhu CPU
    """
    temp_info = {
        "temperature": None,
        "unit": "C",
        "source": "unknown",
        "warning": False,
        "critical": False
    }
    
    try:
        # Raspberry Pi dengan vcgencmd
        if env.get("is_rpi") and is_command_available("vcgencmd"):
            result = run("vcgencmd measure_temp 2>/dev/null")
            if result and result.stdout:
                temp_str = result.stdout.strip()
                if "temp=" in temp_str:
                    temp = float(temp_str.replace("temp=", "").replace("'C", ""))
                    temp_info["temperature"] = temp
                    temp_info["source"] = "vcgencmd"
                    temp_info["warning"] = temp > 70.0
                    temp_info["critical"] = temp > 85.0
        
        # Linux dengan thermal sensors
        elif sys.platform == "linux":
            thermal_zones = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/hwmon/hwmon0/temp1_input",
                "/sys/class/hwmon/hwmon1/temp1_input",
            ]
            
            for zone in thermal_zones:
                if os.path.exists(zone):
                    try:
                        with open(zone, 'r') as f:
                            temp_millic = int(f.read().strip())
                            temp = temp_millic / 1000.0
                            temp_info["temperature"] = temp
                            temp_info["source"] = zone
                            temp_info["warning"] = temp > 70.0
                            temp_info["critical"] = temp > 85.0
                            break
                    except:
                        continue
        
        # macOS dengan powermetrics
        elif sys.platform == "darwin":
            if is_command_available("powermetrics"):
                result = run("sudo powermetrics --samplers smc -i1 -n1 2>/dev/null")
                if result and result.stdout:
                    for line in result.stdout.split('\n'):
                        if "CPU die temperature" in line:
                            temp = float(line.split(':')[-1].strip().replace('C', ''))
                            temp_info["temperature"] = temp
                            temp_info["source"] = "powermetrics"
                            break
        
        # Windows dengan wmic
        elif sys.platform == "win32":
            result = run("wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature /value")
            if result and result.stdout:
                for line in result.stdout.split('\n'):
                    if "CurrentTemperature" in line:
                        try:
                            temp_kelvin = int(line.split('=')[-1].strip())
                            temp = (temp_kelvin / 10.0) - 273.15
                            temp_info["temperature"] = round(temp, 1)
                            temp_info["source"] = "wmic"
                        except:
                            pass
    
    except Exception as e:
        print(f"[WARNING] Error getting CPU temp: {e}", file=sys.stderr)
    
    return temp_info


def get_uptime() -> dict:
    """
    Mendapatkan waktu aktif (uptime) sistem dalam berbagai format.
    
    Returns:
        dict: Informasi uptime
    """
    uptime_info = {
        "seconds": 0,
        "formatted": "Unknown",
        "boot_time": None,
        "days": 0,
        "hours": 0,
        "minutes": 0
    }
    
    try:
        if sys.platform == "linux":
            if os.path.exists("/proc/uptime"):
                with open("/proc/uptime", "r") as f:
                    seconds = float(f.read().split()[0])
                uptime_info["seconds"] = seconds
                
                # Hitung waktu boot
                boot_time = time.time() - seconds
                uptime_info["boot_time"] = datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S")
                
                # Format human readable
                days = int(seconds // 86400)
                hours = int((seconds % 86400) // 3600)
                minutes = int((seconds % 3600) // 60)
                
                uptime_info["days"] = days
                uptime_info["hours"] = hours
                uptime_info["minutes"] = minutes
                
                parts = []
                if days > 0:
                    parts.append(f"{days} day{'s' if days != 1 else ''}")
                if hours > 0:
                    parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
                if minutes > 0 or not parts:
                    parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                
                uptime_info["formatted"] = ", ".join(parts)
        
        elif sys.platform == "darwin":
            result = run("sysctl -n kern.boottime 2>/dev/null")
            if result and result.stdout:
                try:
                    boot_timestamp = int(result.stdout.split()[3].strip(','))
                    uptime_seconds = time.time() - boot_timestamp
                    uptime_info["seconds"] = uptime_seconds
                    
                    # Format sama seperti Linux
                    days = int(uptime_seconds // 86400)
                    hours = int((uptime_seconds % 86400) // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    
                    parts = []
                    if days > 0:
                        parts.append(f"{days} day{'s' if days != 1 else ''}")
                    if hours > 0:
                        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
                    if minutes > 0 or not parts:
                        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                    
                    uptime_info["formatted"] = ", ".join(parts)
                    uptime_info["boot_time"] = datetime.fromtimestamp(boot_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
        
        elif sys.platform == "win32":
            result = run("powershell -Command \"(get-date) - (gcim Win32_OperatingSystem).LastBootUpTime\"")
            if result and result.stdout:
                try:
                    # Parse PowerShell output
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Days' in line and 'Hours' in line and 'Minutes' in line:
                            parts = line.split(',')
                            days = int(parts[0].split(':')[1].strip())
                            hours = int(parts[1].split(':')[1].strip())
                            minutes = int(parts[2].split(':')[1].strip())
                            
                            uptime_info["days"] = days
                            uptime_info["hours"] = hours
                            uptime_info["minutes"] = minutes
                            uptime_info["seconds"] = (days * 86400) + (hours * 3600) + (minutes * 60)
                            
                            parts_str = []
                            if days > 0:
                                parts_str.append(f"{days} day{'s' if days != 1 else ''}")
                            if hours > 0:
                                parts_str.append(f"{hours} hour{'s' if hours != 1 else ''}")
                            if minutes > 0 or not parts_str:
                                parts_str.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                            
                            uptime_info["formatted"] = ", ".join(parts_str)
                            break
                except:
                    pass
    
    except Exception as e:
        print(f"[WARNING] Error getting uptime: {e}", file=sys.stderr)
    
    return uptime_info


def get_cpu_load() -> dict:
    """
    Mendapatkan informasi beban CPU.
    
    Returns:
        dict: Informasi load CPU
    """
    load_info = {
        "load_1min": 0,
        "load_5min": 0,
        "load_15min": 0,
        "cpu_percent": 0,
        "cores": os.cpu_count() or 1,
        "load_per_core": []
    }
    
    try:
        # Load average (Linux, macOS)
        if hasattr(os, 'getloadavg'):
            load_1, load_5, load_15 = os.getloadavg()
            load_info["load_1min"] = round(load_1, 2)
            load_info["load_5min"] = round(load_5, 2)
            load_info["load_15min"] = round(load_15, 2)
        
        # CPU percent menggunakan psutil jika tersedia
        try:
            import psutil
            load_info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            
            # Per-core usage
            load_info["load_per_core"] = psutil.cpu_percent(percpu=True, interval=0.1)
            
            # Jika psutil tersedia, dapatkan informasi tambahan
            load_info["cpu_freq"] = psutil.cpu_freq().current if psutil.cpu_freq() else None
            load_info["cpu_times"] = psutil.cpu_times_percent(interval=0.1)._asdict()
            
        except ImportError:
            # Fallback untuk Windows tanpa psutil
            if sys.platform == "win32":
                result = run("wmic cpu get loadpercentage 2>/dev/null")
                if result and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        try:
                            load_info["cpu_percent"] = float(lines[1].strip())
                        except:
                            pass
        
        # Hitung load normalized (load average dibagi jumlah core)
        if load_info["load_1min"] > 0:
            load_info["load_normalized_1min"] = round(load_info["load_1min"] / load_info["cores"], 2)
            load_info["load_normalized_5min"] = round(load_info["load_5min"] / load_info["cores"], 2)
            load_info["load_normalized_15min"] = round(load_info["load_15min"] / load_info["cores"], 2)
    
    except Exception as e:
        print(f"[WARNING] Error getting CPU load: {e}", file=sys.stderr)
    
    return load_info


def get_memory_usage() -> dict:
    """
    Mendapatkan informasi penggunaan memori.
    
    Returns:
        dict: Informasi memori
    """
    mem_info = {
        "total_mb": 0,
        "available_mb": 0,
        "used_mb": 0,
        "free_mb": 0,
        "percent_used": 0,
        "swap_total_mb": 0,
        "swap_used_mb": 0,
        "swap_free_mb": 0,
        "swap_percent": 0
    }
    
    try:
        # Gunakan psutil jika tersedia
        try:
            import psutil
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            mem_info["total_mb"] = memory.total // (1024 * 1024)
            mem_info["available_mb"] = memory.available // (1024 * 1024)
            mem_info["used_mb"] = memory.used // (1024 * 1024)
            mem_info["free_mb"] = memory.free // (1024 * 1024)
            mem_info["percent_used"] = memory.percent
            
            mem_info["swap_total_mb"] = swap.total // (1024 * 1024)
            mem_info["swap_used_mb"] = swap.used // (1024 * 1024)
            mem_info["swap_free_mb"] = swap.free // (1024 * 1024)
            mem_info["swap_percent"] = swap.percent
            
        except ImportError:
            # Fallback untuk Linux tanpa psutil
            if sys.platform == "linux" and os.path.exists("/proc/meminfo"):
                mem_data = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        key, value = line.split(":", 1)
                        mem_data[key.strip()] = int(value.strip().split()[0])
                
                # Hitung dalam MB
                total = mem_data.get("MemTotal", 0) // 1024
                free = mem_data.get("MemFree", 0) // 1024
                buffers = mem_data.get("Buffers", 0) // 1024
                cached = mem_data.get("Cached", 0) // 1024
                
                used = total - free - buffers - cached
                available = free + buffers + cached
                
                mem_info["total_mb"] = total
                mem_info["available_mb"] = available
                mem_info["used_mb"] = used
                mem_info["free_mb"] = free
                mem_info["percent_used"] = round((used / total) * 100, 1) if total > 0 else 0
                
                # Swap
                swap_total = mem_data.get("SwapTotal", 0) // 1024
                swap_free = mem_data.get("SwapFree", 0) // 1024
                swap_used = swap_total - swap_free
                
                mem_info["swap_total_mb"] = swap_total
                mem_info["swap_used_mb"] = swap_used
                mem_info["swap_free_mb"] = swap_free
                mem_info["swap_percent"] = round((swap_used / swap_total) * 100, 1) if swap_total > 0 else 0
            
            elif sys.platform == "win32":
                # Windows dengan wmic
                result = run("wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value")
                if result and result.stdout:
                    data = {}
                    for line in result.stdout.strip().split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            data[key.strip()] = int(value.strip())
                    
                    total_kb = data.get("TotalVisibleMemorySize", 0)
                    free_kb = data.get("FreePhysicalMemory", 0)
                    
                    mem_info["total_mb"] = total_kb // 1024
                    mem_info["free_mb"] = free_kb // 1024
                    mem_info["used_mb"] = (total_kb - free_kb) // 1024
                    mem_info["available_mb"] = free_kb // 1024
                    mem_info["percent_used"] = round(((total_kb - free_kb) / total_kb) * 100, 1) if total_kb > 0 else 0
    
    except Exception as e:
        print(f"[WARNING] Error getting memory info: {e}", file=sys.stderr)
    
    return mem_info


def get_disk_usage(project_dir: str = None) -> dict:
    """
    Mendapatkan informasi penggunaan disk.
    
    Args:
        project_dir (str): Direktori proyek untuk memeriksa disk usage khusus
        
    Returns:
        dict: Informasi disk usage
    """
    disk_info = {
        "total_gb": 0,
        "used_gb": 0,
        "free_gb": 0,
        "percent_used": 0,
        "project_dir_usage": 0,
        "project_dir_path": project_dir
    }
    
    try:
        if project_dir is None:
            from core.env_tools import project_root
            project_dir = project_root()
        
        # Gunakan psutil jika tersedia
        try:
            import psutil
            disk = psutil.disk_usage('/')
            
            disk_info["total_gb"] = round(disk.total / (1024**3), 1)
            disk_info["used_gb"] = round(disk.used / (1024**3), 1)
            disk_info["free_gb"] = round(disk.free / (1024**3), 1)
            disk_info["percent_used"] = disk.percent
            
            # Hitung ukuran direktori proyek
            try:
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(project_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                disk_info["project_dir_usage"] = round(total_size / (1024**2), 2)  # MB
            except:
                disk_info["project_dir_usage"] = 0
            
        except ImportError:
            # Fallback tanpa psutil
            if sys.platform == "linux" or sys.platform == "darwin":
                result = run("df -h / | tail -1")
                if result and result.stdout:
                    parts = result.stdout.strip().split()
                    if len(parts) >= 5:
                        try:
                            disk_info["total_gb"] = parts[1]
                            disk_info["used_gb"] = parts[2]
                            disk_info["free_gb"] = parts[3]
                            disk_info["percent_used"] = parts[4].replace('%', '')
                        except:
                            pass
    
    except Exception as e:
        print(f"[WARNING] Error getting disk info: {e}", file=sys.stderr)
    
    return disk_info


def check_service_status(service_name: str, env: dict) -> dict:
    """
    Memeriksa status service.
    
    Args:
        service_name (str): Nama service
        env (dict): Environment dictionary
        
    Returns:
        dict: Status service
    """
    status = {
        "service": service_name,
        "running": False,
        "active": False,
        "pid": None,
        "uptime": None,
        "details": {}
    }
    
    try:
        if sys.platform == "linux":
            # Cek dengan systemctl jika tersedia
            if is_command_available("systemctl"):
                result = run(f"systemctl is-active {service_name} 2>/dev/null")
                if result and result.returncode == 0:
                    status["active"] = True
                    status["details"]["systemd"] = "active"
            
            # Cek dengan service command
            if is_command_available("service"):
                result = run(f"service {service_name} status 2>/dev/null")
                if result:
                    status["details"]["service_cmd"] = result.stdout[:200]
            
            # Cek PID dengan pgrep
            result = run(f"pgrep -f {service_name} 2>/dev/null")
            if result and result.stdout:
                pids = result.stdout.strip().split()
                if pids:
                    status["running"] = True
                    status["pid"] = pids[0]
                    
                    # Cek uptime proses
                    try:
                        pid = int(pids[0])
                        proc_path = f"/proc/{pid}"
                        if os.path.exists(proc_path):
                            start_time = os.path.getctime(f"/proc/{pid}")
                            uptime_seconds = time.time() - start_time
                            hours = int(uptime_seconds // 3600)
                            minutes = int((uptime_seconds % 3600) // 60)
                            status["uptime"] = f"{hours}h {minutes}m"
                    except:
                        pass
        
        elif sys.platform == "win32":
            result = run(f"tasklist /FI \"IMAGENAME eq {service_name}.exe\" 2>nul")
            if result and service_name.lower() in result.stdout.lower():
                status["running"] = True
        
        elif sys.platform == "darwin":
            result = run(f"ps aux | grep -i {service_name} | grep -v grep")
            if result and result.stdout:
                status["running"] = True
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split()
                    if len(parts) > 1:
                        status["pid"] = parts[1]
    
    except Exception as e:
        print(f"[WARNING] Error checking service {service_name}: {e}", file=sys.stderr)
    
    return status


def check_port_status(port: int = 5000, host: str = "127.0.0.1") -> dict:
    """
    Memeriksa status port.
    
    Args:
        port (int): Port number
        host (str): Host address
        
    Returns:
        dict: Status port
    """
    port_status = {
        "port": port,
        "host": host,
        "open": False,
        "service": "unknown",
        "response_time": None,
        "error": None
    }
    
    try:
        # Coba koneksi dengan timeout
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        result = sock.connect_ex((host, port))
        response_time = (time.time() - start_time) * 1000  # ms
        
        sock.close()
        
        port_status["open"] = result == 0
        port_status["response_time"] = round(response_time, 2)
        
        # Coba identifikasi service
        try:
            service = socket.getservbyport(port)
            port_status["service"] = service
        except:
            # Port mapping default
            if port == 80:
                port_status["service"] = "http"
            elif port == 443:
                port_status["service"] = "https"
            elif port == 22:
                port_status["service"] = "ssh"
            elif port == 3306:
                port_status["service"] = "mysql"
            elif port == 5432:
                port_status["service"] = "postgresql"
            elif port == 5000:
                port_status["service"] = "flask_dev"
            elif port == 8000:
                port_status["service"] = "http_alt"
    
    except socket.timeout:
        port_status["error"] = "timeout"
    except ConnectionRefusedError:
        port_status["error"] = "connection_refused"
    except Exception as e:
        port_status["error"] = str(e)
    
    return port_status


def get_system_stats(env: dict, project_dir: str = None) -> dict:
    """
    Mendapatkan semua statistik sistem.
    
    Args:
        env (dict): Environment dictionary
        project_dir (str): Direktori proyek
        
    Returns:
        dict: Semua statistik sistem
    """
    stats = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "os": env.get("os", "unknown"),
            "platform": env.get("platform", "unknown"),
            "hostname": socket.gethostname(),
            "uptime": get_uptime(),
            "cpu_info": get_cpu_load(),
            "memory_info": get_memory_usage(),
            "disk_info": get_disk_usage(project_dir),
            "cpu_temp": get_cpu_temp(env),
            "ips": get_ip()
        },
        "services": {
            "gunicorn": check_service_status("gunicorn", env),
            "nginx": check_service_status("nginx", env),
            "supervisor": check_service_status("supervisord", env)
        },
        "ports": {
            "5000": check_port_status(5000),
            "80": check_port_status(80),
            "443": check_port_status(443)
        },
        "bms_app": {
            "port_5000": check_port_status(5000),
            "project_dir": project_dir or "unknown",
            "python_version": sys.version.split()[0]
        }
    }
    
    return stats


def monitoring(env: dict, project_dir: str = None):
    """
    Menampilkan informasi monitoring sistem secara keseluruhan.
    
    Args:
        env (dict): Environment dictionary
        project_dir (str): Direktori proyek
    """
    from colorama import init, Fore, Style
    init(autoreset=True)
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}BMS SYSTEM MONITORING")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # Dapatkan semua statistik
    stats = get_system_stats(env, project_dir)
    
    # Tampilkan informasi sistem
    print(f"\n{Fore.GREEN}{Style.BRIGHT}📊 SISTEM DASAR{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    print(f"OS            : {stats['system']['os']}")
    print(f"Hostname      : {stats['system']['hostname']}")
    print(f"Uptime        : {stats['system']['uptime']['formatted']}")
    print(f"Boot Time     : {stats['system']['uptime'].get('boot_time', 'N/A')}")
    
    # IP Addresses
    ips = stats['system']['ips']
    print(f"\n{Fore.GREEN}{Style.BRIGHT}🌐 JARINGAN{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    print(f"Local IP      : {ips.get('local_ip', '127.0.0.1')}")
    if ips.get('public_ip'):
        print(f"Public IP     : {ips['public_ip']}")
    if ips.get('all_ips'):
        print(f"All IPs       : {', '.join(ips['all_ips'][:3])}")
    
    # CPU
    cpu = stats['system']['cpu_info']
    print(f"\n{Fore.GREEN}{Style.BRIGHT}💻 CPU{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    print(f"Cores         : {cpu['cores']}")
    print(f"Load (1/5/15) : {cpu['load_1min']}, {cpu['load_5min']}, {cpu['load_15min']}")
    if cpu.get('load_normalized_1min'):
        print(f"Load/CPU      : {cpu['load_normalized_1min']}, {cpu['load_normalized_5min']}, {cpu['load_normalized_15min']}")
    print(f"Usage %       : {cpu['cpu_percent']}%")
    
    # Memory
    mem = stats['system']['memory_info']
    print(f"\n{Fore.GREEN}{Style.BRIGHT}💾 MEMORI{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    print(f"Total         : {mem['total_mb']} MB")
    print(f"Used          : {mem['used_mb']} MB ({mem['percent_used']}%)")
    print(f"Available     : {mem['available_mb']} MB")
    if mem['swap_total_mb'] > 0:
        print(f"Swap Used     : {mem['swap_used_mb']} MB ({mem['swap_percent']}%)")
    
    # Disk
    disk = stats['system']['disk_info']
    if disk['total_gb']:
        print(f"\n{Fore.GREEN}{Style.Bright}💿 DISK{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'-'*40}")
        print(f"Total         : {disk['total_gb']} GB")
        print(f"Used          : {disk['used_gb']} GB ({disk['percent_used']}%)")
        print(f"Free          : {disk['free_gb']} GB")
        if disk['project_dir_usage']:
            print(f"Project Dir   : {disk['project_dir_usage']} MB")
    
    # CPU Temperature
    temp = stats['system']['cpu_temp']
    if temp['temperature']:
        temp_color = Fore.RED if temp['critical'] else (Fore.YELLOW if temp['warning'] else Fore.GREEN)
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🌡️  SUHU CPU{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'-'*40}")
        print(f"Temperature   : {temp_color}{temp['temperature']}°{temp['unit']}{Style.RESET_ALL}")
        print(f"Source        : {temp['source']}")
    
    # Services
    print(f"\n{Fore.GREEN}{Style.BRIGHT}🛠️  SERVICE STATUS{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    
    for name, service in stats['services'].items():
        status_color = Fore.GREEN if service['running'] else Fore.RED
        status_text = "RUNNING" if service['running'] else "STOPPED"
        
        info = []
        if service['pid']:
            info.append(f"PID: {service['pid']}")
        if service['uptime']:
            info.append(f"Uptime: {service['uptime']}")
        
        info_str = f" ({', '.join(info)})" if info else ""
        
        print(f"{name:12} : {status_color}{status_text}{Style.RESET_ALL}{info_str}")
    
    # Ports
    print(f"\n{Fore.GREEN}{Style.Bright}🔌 PORT STATUS{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    
    for port_num, port_info in stats['ports'].items():
        if port_info['port'] == port_num:
            status_color = Fore.GREEN if port_info['open'] else Fore.RED
            status_text = "OPEN" if port_info['open'] else "CLOSED"
            
            info = [port_info['service']]
            if port_info['response_time']:
                info.append(f"{port_info['response_time']}ms")
            if port_info['error']:
                info.append(f"Error: {port_info['error']}")
            
            info_str = f" ({', '.join(info)})" if info else ""
            
            print(f"Port {port_num:<5} : {status_color}{status_text}{Style.RESET_ALL}{info_str}")
    
    # BMS App Info
    print(f"\n{Fore.GREEN}{Style.Bright}🚀 BMS APPLICATION{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-'*40}")
    
    bms_port = stats['bms_app']['port_5000']
    port_status = "✅ OPEN" if bms_port['open'] else "❌ CLOSED"
    port_color = Fore.GREEN if bms_port['open'] else Fore.RED
    
    print(f"Port 5000     : {port_color}{port_status}{Style.RESET_ALL}")
    print(f"Python        : {stats['bms_app']['python_version']}")
    print(f"Project Dir   : {stats['bms_app']['project_dir']}")
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}Last Update: {stats['timestamp']}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Return stats untuk penggunaan programmatic
    return stats


def save_monitoring_data(stats: dict, log_dir: str = None):
    """
    Menyimpan data monitoring ke file JSON.
    
    Args:
        stats (dict): Data statistik
        log_dir (str): Direktori log
    """
    if log_dir is None:
        from core.env_tools import project_root
        log_dir = os.path.join(project_root(), "logs")
    
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"monitoring_{datetime.now().strftime('%Y%m%d')}.json")
    
    try:
        # Baca data existing jika ada
        existing_data = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                existing_data = json.load(f)
        
        # Tambah data baru
        existing_data.append(stats)
        
        # Simpan (maks 1000 entri per file)
        if len(existing_data) > 1000:
            existing_data = existing_data[-1000:]
        
        with open(log_file, 'w') as f:
            json.dump(existing_data, f, indent=2, default=str)
        
        return log_file
    except Exception as e:
        print(f"[WARNING] Error saving monitoring data: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    # Test fungsi monitoring
    from core.detect_os import detail_os
    env_info = detail_os()
    monitoring(env_info)