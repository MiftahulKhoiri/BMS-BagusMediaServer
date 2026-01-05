import os
import subprocess
import shlex

def run(cmd: str) -> int:
    """
    Menjalankan perintah dan menampilkan output log secara real-time.
    
    Args:
        cmd (str): Perintah shell yang akan dijalankan.
    
    Returns:
        int: Exit code dari proses yang dijalankan.
    """
    print(f"[RUN] {cmd}\n")

    try:
        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )

        # Membaca dan menampilkan output secara real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        return process.poll()  # Return exit code
    except Exception as e:
        print(f"[ERROR] Gagal menjalankan perintah: {e}")
        return 1  # Return non-zero exit code untuk menandakan error

def fix_permissions(path: str) -> int:
    """
    Memperbaiki permission folder dengan menetapkan mode 755 (rwxr-xr-x)
    secara rekursif. Hanya berfungsi pada sistem POSIX (Linux/macOS).
    
    Args:
        path (str): Path ke folder yang akan diperbaiki permission-nya.
    
    Returns:
        int: Exit code dari proses chmod.
    """
    if os.name != "posix":
        print("[!] Permission fix hanya untuk POSIX (Linux/macOS).")
        return 1
    
    if not os.path.exists(path):
        print(f"[!] Path tidak ditemukan: {path}")
        return 1
    
    return run(f"sudo chmod -R 755 {path}")