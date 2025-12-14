# core/system_tools.py
import os
import subprocess
import shutil
import shlex

def run(cmd: str):
    """
    Menjalankan perintah shell dan menampilkan output secara real-time.
    Fungsi ini memecah perintah string menjadi argument list dan menjalankannya
    dengan subprocess, menampilkan output baris per baris saat proses berjalan.
    
    Args:
        cmd (str): Perintah shell yang akan dijalankan.
    
    Note:
        - Menggunakan shlex.split() untuk memecah string dengan aman
        - Menggabungkan stdout dan stderr ke aliran yang sama
        - Menampilkan output secara real-time (line-by-line)
    """
    print(f"[RUN] {cmd}\n")

    # Membagi perintah string menjadi list argument dengan aman
    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Gabungkan stderr ke stdout
        bufsize=1,                 # Line-buffered
        universal_newlines=True    # Mengembalikan string bukan bytes
    )

    # Membaca dan menampilkan output secara real-time
    for line in process.stdout:
        print(line, end="")  # langsung tampil ke terminal

    # Menunggu proses selesai
    process.wait()


def fix_permissions(path: str):
    """
    Memperbaiki permission folder dengan menetapkan mode 755 (rwxr-xr-x)
    secara rekursif. Hanya berfungsi pada sistem POSIX (Linux/macOS).
    
    Args:
        path (str): Path ke folder yang akan diperbaiki permission-nya.
    
    Note:
        - Menggunakan sudo untuk memastikan permission dapat diubah
        - Mode 755 memberikan akses baca+eksekusi ke semua user
          dan akses tulis hanya ke owner
    """
    if os.name != "posix":
        print("[!] Permission fix hanya untuk POSIX (Linux/macOS).")
        return
    
    run(f"sudo chmod -R 755 {path}")