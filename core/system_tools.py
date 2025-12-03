# core/system_tools.py
import os
import subprocess
import shutil

def run(cmd: str, check: bool = False):
    """
    Jalankan perintah shell dan tampilkan output.
    Jika check=True, raise CalledProcessError saat gagal.
    """
    print(f"[cmd] {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[!] Command error (code {result.returncode}): {cmd}")
        if check:
            raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.returncode


def fix_permissions(path: str):
    """Perbaiki permission folder (Linux only)."""
    if os.name != "posix":
        print("[!] Permission fix hanya untuk POSIX (Linux/macOS).")
        return
    run(f"sudo chmod -R 755 {path}")