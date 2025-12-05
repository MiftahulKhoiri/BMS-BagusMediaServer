# core/system_tools.py
import os
import subprocess
import shutil
import shlex

def run(cmd: str):
    """
    Menjalankan perintah dan menampilkan output log secara real-time.
    """
    print(f"[RUN] {cmd}\n")

    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )

    # STREAM REAL-TIME
    for line in process.stdout:
        print(line, end="")  # langsung tampil ke terminal

    process.wait()


def fix_permissions(path: str):
    """Perbaiki permission folder (Linux only)."""
    if os.name != "posix":
        print("[!] Permission fix hanya untuk POSIX (Linux/macOS).")
        return
    run(f"sudo chmod -R 755 {path}")