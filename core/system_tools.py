# core/system_tools.py
import os
import sys
import subprocess
from typing import Optional, Tuple, List

def run(cmd: str, cwd: Optional[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Menjalankan perintah shell dengan error handling yang lebih baik.
    
    Args:
        cmd (str): Perintah shell yang akan dijalankan
        cwd (str, optional): Working directory
        timeout (int): Timeout dalam detik
    
    Returns:
        subprocess.CompletedProcess: Hasil eksekusi perintah
    """
    try:
        # Set default cwd ke project root
        if cwd is None:
            from core.env_tools import project_root
            cwd = project_root()
        
        # Jalankan perintah
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='ignore'
        )
        
        return result
        
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds"
        )
    except Exception as e:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=-1,
            stdout="",
            stderr=str(e)
        )

def is_command_available(cmd: str) -> bool:
    """
    Mengecek apakah suatu perintah tersedia di PATH.
    
    Args:
        cmd (str): Nama perintah yang akan dicek
    
    Returns:
        bool: True jika perintah tersedia
    """
    return shutil.which(cmd) is not None

def get_command_path(cmd: str) -> Optional[str]:
    """
    Mendapatkan path lengkap dari suatu perintah.
    
    Args:
        cmd (str): Nama perintah
    
    Returns:
        str: Path lengkap ke perintah, atau None jika tidak ditemukan
    """
    return shutil.which(cmd)

def run_with_output(cmd: str, cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Menjalankan perintah dan mengembalikan output secara real-time.
    
    Args:
        cmd (str): Perintah shell
        cwd (str, optional): Working directory
    
    Returns:
        tuple: (returncode, stdout, stderr)
    """
    try:
        from core.env_tools import project_root
        cwd = cwd or project_root()
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # Baca output secara real-time
        while True:
            output = process.stdout.readline()
            if output:
                stdout_lines.append(output)
                print(output, end='')
            
            error = process.stderr.readline()
            if error:
                stderr_lines.append(error)
                print(error, end='', file=sys.stderr)
            
            if process.poll() is not None:
                break
        
        # Baca sisa output
        for output in process.stdout.readlines():
            stdout_lines.append(output)
            print(output, end='')
        
        for error in process.stderr.readlines():
            stderr_lines.append(error)
            print(error, end='', file=sys.stderr)
        
        returncode = process.wait()
        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)
        
        return returncode, stdout, stderr
        
    except Exception as e:
        print(f"[ERROR] Failed to run command: {e}", file=sys.stderr)
        return -1, "", str(e)

def run_sudo(cmd: str, password: Optional[str] = None, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """
    Menjalankan perintah dengan sudo.
    
    Args:
        cmd (str): Perintah yang akan dijalankan
        password (str, optional): Password sudo (tidak disarankan)
        cwd (str, optional): Working directory
    
    Returns:
        subprocess.CompletedProcess: Hasil eksekusi
    """
    # Jika di Windows, jalankan tanpa sudo
    if sys.platform == "win32":
        return run(cmd, cwd=cwd)
    
    # Jika di Termux, jalankan tanpa sudo
    if "termux" in sys.executable or os.path.exists("/data/data/com.termux"):
        return run(cmd, cwd=cwd)
    
    sudo_cmd = f"sudo {cmd}"
    
    if password:
        # Method dengan echo password (kurang aman)
        sudo_cmd = f"echo {password} | sudo -S {cmd}"
    
    return run(sudo_cmd, cwd=cwd)

def kill_process(process_name: str, signal: str = "TERM") -> bool:
    """
    Menghentikan proses berdasarkan nama.
    
    Args:
        process_name (str): Nama proses
        signal (str): Signal yang akan dikirim (TERM, KILL, HUP)
    
    Returns:
        bool: True jika berhasil menghentikan proses
    """
    try:
        if sys.platform == "win32":
            # Windows
            cmd = f"taskkill /F /IM {process_name}"
        else:
            # Unix-like
            sig_map = {"TERM": 15, "KILL": 9, "HUP": 1}
            sig_num = sig_map.get(signal.upper(), 15)
            cmd = f"pkill -{sig_num} -f {process_name}"
        
        result = run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Failed to kill process {process_name}: {e}")
        return False

def get_pids_by_name(process_name: str) -> List[int]:
    """
    Mendapatkan daftar PID berdasarkan nama proses.
    
    Args:
        process_name (str): Nama proses
    
    Returns:
        list: Daftar PID
    """
    pids = []
    try:
        if sys.platform == "win32":
            cmd = f"tasklist /FI \"IMAGENAME eq {process_name}\" /FO CSV /NH"
            result = run(cmd)
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.strip('"').split('","')
                    if len(parts) > 1:
                        try:
                            pids.append(int(parts[1]))
                        except ValueError:
                            pass
        else:
            cmd = f"pgrep -f {process_name}"
            result = run(cmd)
            if result.stdout:
                for pid_str in result.stdout.strip().split():
                    try:
                        pids.append(int(pid_str))
                    except ValueError:
                        pass
        
        return pids
    except Exception as e:
        print(f"[ERROR] Failed to get PIDs for {process_name}: {e}")
        return []

def create_directory(path: str, mode: int = 0o755) -> bool:
    """
    Membuat direktori dengan permission yang ditentukan.
    
    Args:
        path (str): Path direktori
        mode (int): Permission mode (octal)
    
    Returns:
        bool: True jika berhasil
    """
    try:
        os.makedirs(path, mode=mode, exist_ok=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create directory {path}: {e}")
        return False

def copy_file(src: str, dst: str, overwrite: bool = True) -> bool:
    """
    Menyalin file dari src ke dst.
    
    Args:
        src (str): Source file path
        dst (str): Destination file path
        overwrite (bool): Overwrite jika file sudah ada
    
    Returns:
        bool: True jika berhasil
    """
    try:
        if not os.path.exists(src):
            print(f"[ERROR] Source file does not exist: {src}")
            return False
        
        if os.path.exists(dst) and not overwrite:
            print(f"[WARNING] Destination file already exists: {dst}")
            return False
        
        # Buat direktori tujuan jika belum ada
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            create_directory(dst_dir)
        
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to copy file {src} to {dst}: {e}")
        return False

def move_file(src: str, dst: str, overwrite: bool = True) -> bool:
    """
    Memindahkan file dari src ke dst.
    
    Args:
        src (str): Source file path
        dst (str): Destination file path
        overwrite (bool): Overwrite jika file sudah ada
    
    Returns:
        bool: True jika berhasil
    """
    try:
        if not os.path.exists(src):
            print(f"[ERROR] Source file does not exist: {src}")
            return False
        
        if os.path.exists(dst) and not overwrite:
            print(f"[WARNING] Destination file already exists: {dst}")
            return False
        
        # Buat direktori tujuan jika belum ada
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            create_directory(dst_dir)
        
        shutil.move(src, dst)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to move file {src} to {dst}: {e}")
        return False

def delete_file(path: str) -> bool:
    """
    Menghapus file.
    
    Args:
        path (str): Path file
    
    Returns:
        bool: True jika berhasil
    """
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to delete file {path}: {e}")
        return False

def delete_directory(path: str, recursive: bool = True) -> bool:
    """
    Menghapus direktori.
    
    Args:
        path (str): Path direktori
        recursive (bool): Hapus secara rekursif
    
    Returns:
        bool: True jika berhasil
    """
    try:
        if os.path.exists(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to delete directory {path}: {e}")
        return False

def get_file_size(path: str) -> Optional[int]:
    """
    Mendapatkan ukuran file dalam bytes.
    
    Args:
        path (str): Path file
    
    Returns:
        int: Ukuran file dalam bytes, atau None jika error
    """
    try:
        if os.path.exists(path):
            return os.path.getsize(path)
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get file size {path}: {e}")
        return None

def read_file(path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Membaca isi file.
    
    Args:
        path (str): Path file
        encoding (str): Encoding file
    
    Returns:
        str: Isi file, atau None jika error
    """
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read file {path}: {e}")
        return None

def write_file(path: str, content: str, mode: str = 'w', encoding: str = 'utf-8') -> bool:
    """
    Menulis konten ke file.
    
    Args:
        path (str): Path file
        content (str): Konten yang akan ditulis
        mode (str): Mode penulisan ('w' untuk write, 'a' untuk append)
        encoding (str): Encoding file
    
    Returns:
        bool: True jika berhasil
    """
    try:
        # Buat direktori jika belum ada
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            create_directory(dir_path)
        
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write file {path}: {e}")
        return False

def execute_python_script(script_path: str, args: List[str] = None, venv_python: str = None) -> subprocess.CompletedProcess:
    """
    Menjalankan script Python.
    
    Args:
        script_path (str): Path ke script Python
        args (list): Argument untuk script
        venv_python (str): Python executable dari virtual environment
    
    Returns:
        subprocess.CompletedProcess: Hasil eksekusi
    """
    try:
        if args is None:
            args = []
        
        if venv_python:
            cmd = [venv_python, script_path] + args
        else:
            cmd = [sys.executable, script_path] + args
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
    except Exception as e:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=-1,
            stdout="",
            stderr=str(e)
        )

def check_dependencies(dependencies: List[str]) -> dict:
    """
    Mengecek ketersediaan dependencies.
    
    Args:
        dependencies (list): List nama dependencies/modules
    
    Returns:
        dict: Status setiap dependency
    """
    results = {}
    
    for dep in dependencies:
        if dep.startswith("python:"):
            # Python module
            module_name = dep.split(":", 1)[1]
            try:
                __import__(module_name)
                results[dep] = {
                    "available": True,
                    "type": "python_module"
                }
            except ImportError:
                results[dep] = {
                    "available": False,
                    "type": "python_module"
                }
        else:
            # System command
            results[dep] = {
                "available": is_command_available(dep),
                "type": "system_command"
            }
    
    return results

# Import shutil untuk fungsi yang membutuhkan
import shutil

if __name__ == "__main__":
    # Test fungsi-fungsi
    print("Testing system_tools...")
    
    # Test run command
    result = run("echo Hello World")
    print(f"Run echo: {result.stdout.strip()}")
    
    # Test is_command_available
    print(f"Is python available: {is_command_available('python')}")
    print(f"Is python3 available: {is_command_available('python3')}")
    print(f"Is fakecmd available: {is_command_available('fakecmd')}")
    
    # Test get_command_path
    print(f"Python path: {get_command_path('python')}")
    
    # Test check_dependencies
    deps = ["python:os", "python:sys", "python:flask", "ls", "curl"]
    print(f"Dependency check: {check_dependencies(deps)}")