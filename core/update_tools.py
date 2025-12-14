# Tambahkan import yang diperlukan
import subprocess

# Perbaiki git_pull() untuk menggunakan run() yang benar
def git_pull(project_dir: str) -> bool:
    """Menjalankan git pull di direktori project."""

    print("[i] Menarik update dari Git (git pull)...")

    if not git_available():
        print("[!] Git tidak ditemukan di sistem.")
        return False

    cur = os.getcwd()
    try:
        os.chdir(project_dir)
        # Gunakan run() yang mengembalikan exit code
        exit_code = run("git pull")
        return exit_code == 0
    except Exception as e:
        print(f"[ERROR] Gagal menjalankan git pull: {e}")
        return False
    finally:
        os.chdir(cur)

# Perbaiki force_update() untuk menggunakan run() yang benar
def force_update(env: dict, project_dir: str):
    """
    Force update:
    - Menghapus semua perubahan lokal
    - Membersihkan file yang tidak ada di GitHub
    - Menarik ulang versi GitHub
    - Install dependencies
    """
    print("====== BMS FORCE UPDATE ======")
    print("[!] PERINGATAN: Semua perubahan lokal AKAN DIHAPUS.")
    print("[!] Folder project akan disamakan 100% dengan GitHub.\n")

    if not git_available():
        print("[!] Git tidak tersedia. Tidak dapat melakukan Force Update.")
        return

    cur = os.getcwd()
    try:
        os.chdir(project_dir)

        print("[+] Reset perubahan lokal...")
        run("git reset --hard HEAD")

        print("[+] Membersihkan file yang tidak ter-tracked...")
        run("git clean -fd")

        print("[+] Menarik update terbaru...")
        exit_code = run("git pull")
        if exit_code != 0:
            print("[!] Gagal menarik update GitHub.")
            return

    except Exception as e:
        print(f"[ERROR] Gagal melakukan force update: {e}")
        return
    finally:
        os.chdir(cur)