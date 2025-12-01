import os
import subprocess
from flask import Blueprint, jsonify, session, render_template, current_app
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import BASE
import requests
from app.BMS_config import BMS_load_version
import zipfile
import shutil
from datetime import datetime


update = Blueprint("update", __name__, url_prefix="/update")

# Path default
UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# ---------------------------------------------------------
#  Helper hak akses
# ---------------------------------------------------------
def BMS_update_required_simple():
    """Cek apakah user boleh update (admin atau root)."""
    if not BMS_auth_is_login():
        return False
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return False
    return True

# ---------------------------------------------------------
#  CEK UPDATE via GitHub API (Mode Universal)
# ---------------------------------------------------------

GITHUB_API_COMMITS = "https://api.github.com/repos/MiftahulKhoiri/BMS-BagusMediaServer/commits?per_page=1"

def BMS_check_update():
    """Cek commit terbaru dari GitHub dan bandingkan dengan versi lokal."""
    
    local_info = BMS_load_version()
    local_commit = local_info.get("commit", "local")
    local_version = local_info.get("version", "1.0.0")

    try:
        response = requests.get(GITHUB_API_COMMITS, timeout=5)
        response.raise_for_status()

        data = response.json()[0]  # Commit terbaru
        remote_commit = data["sha"]
        remote_message = data["commit"]["message"]
        remote_date = data["commit"]["author"]["date"]

        update_available = remote_commit != local_commit

        return {
            "success": True,
            "local_version": local_version,
            "local_commit": local_commit,
            "remote_commit": remote_commit,
            "remote_message": remote_message,
            "remote_date": remote_date,
            "update_available": update_available
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "update_available": False
        }

@update.route("/check-api")
def check_update_api():
    """API untuk cek update via GitHub API."""
    
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403

    info = BMS_check_update()
    return jsonify(info)


GITHUB_ZIP_URL = "https://github.com/MiftahulKhoiri/BMS-BagusMediaServer/archive/refs/heads/main.zip"


@update.route("/start-download")
def start_download():
    """Download ZIP update terbaru dan simpan ke folder UPDATE/"""

    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403

    try:
        # Lokasi file ZIP yang akan disimpan
        zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")

        # Download ZIP
        r = requests.get(GITHUB_ZIP_URL, stream=True)
        r.raise_for_status()

        with open(zip_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

        return jsonify({
            "success": True,
            "zip_path": zip_path,
            "message": "Download ZIP update berhasil"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def extract_update_zip():
    """Extract ZIP update ke folder TEMP."""

    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")
    temp_extract = os.path.join(UPDATE_PATH, "TEMP_EXTRACT")

    # Bersihkan folder TEMP_EXTRACT jika sudah ada
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)

    os.makedirs(temp_extract, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_extract)

        # Folder hasil extract biasanya: BMS-BagusMediaServer-main/
        extracted_root = None
        for name in os.listdir(temp_extract):
            full = os.path.join(temp_extract, name)
            if os.path.isdir(full):
                extracted_root = full
                break

        return True, extracted_root

    except Exception as e:
        return False, str(e)

def backup_current_version():
    """Backup seluruh project kecuali folder UPDATE & BACKUP."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_PATH, f"BMS_backup_{timestamp}.zip")

    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            for root, dirs, files in os.walk(BASE):
                
                # Skip folder UPDATE & BACKUP agar tidak backup diri sendiri
                if "UPDATE" in root or "BACKUP" in root:
                    continue

                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, BASE)
                    backup_zip.write(filepath, arcname)

        return True, backup_file

    except Exception as e:
        return False, str(e)

def replace_with_new_version(extracted_root):
    """Ganti file lama dengan file baru."""

    try:
        for root, dirs, files in os.walk(extracted_root):

            rel_path = os.path.relpath(root, extracted_root)
            target_dir = os.path.join(BASE, rel_path)

            # Buat folder jika belum ada
            os.makedirs(target_dir, exist_ok=True)

            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(target_dir, file)

                # Overwrite file
                shutil.copy2(src, dst)

        return True, "Replace selesai"

    except Exception as e:
        return False, str(e)

@update.route("/apply-update")
def apply_update():
    """Proses utama update: extract → backup → replace → selesai."""
    
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403

    # EXTRACT ZIP
    ok, result = extract_update_zip()
    if not ok:
        return jsonify({"success": False, "step": "extract", "error": result})

    extracted_root = result

    # BACKUP
    ok, backup_info = backup_current_version()
    if not ok:
        return jsonify({"success": False, "step": "backup", "error": backup_info})

    backup_file = backup_info

    # REPLACE
ok, msg = replace_with_new_version(extracted_root)
if not ok:
    return jsonify({"success": False, "step": "replace", "error": msg})

# --- UPDATE VERSION.JSON ---
remote_commit = BMS_check_update()["remote_commit"]
BMS_save_version("1.0.0", remote_commit)

return jsonify({
    "success": True,
    "message": "Update berhasil diterapkan!",
    "backup_file": backup_file,
    "new_commit": remote_commit
})

# ---------------------------------------------------------
#  UI ROUTE
# ---------------------------------------------------------
@update.route("/ui")
def BMS_update_ui():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403
    return render_template("BMS_update.html")


# ---------------------------------------------------------
#  CEK UPDATE via HTTP
# ---------------------------------------------------------
@update.route("/check-update")
def check_update():
    try:
        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            return jsonify({
                "update_available": False,
                "error": "PROJECT_ROOT tidak disetting atau tidak ada"
            }), 500

        subprocess.run(["git", "fetch"], cwd=base_dir)

        status = subprocess.run(
            ["git", "status", "-uno"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )

        update_available = "behind" in status.stdout.lower()

        return jsonify({
            "update_available": update_available,
            "output": status.stdout
        })

    except Exception as e:
        return jsonify({
            "update_available": False,
            "error": str(e)
        }), 500


# ---------------------------------------------------------
#  RESET PERUBAHAN LOKAL SEBELUM PULL
# ---------------------------------------------------------
def safe_reset_before_pull(base_dir):
    """
    Buang semua perubahan lokal:
    - git restore .
    - git clean -fd
    """
    try:
        subprocess.run(["git", "restore", "."], cwd=base_dir, check=False)
        subprocess.run(["git", "clean", "-fd"], cwd=base_dir, check=False)
        return True, "Reset lokal selesai"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------
#  WEBSOCKET: PROSES UPDATE REALTIME
# ---------------------------------------------------------
def register_ws(sock):

    @sock.route("/ws/update")
    def ws_update(ws):

        # Auth
        if not BMS_update_required_simple():
            ws.send("[ERROR] Tidak punya izin update (admin/root saja)")
            return

        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            ws.send("[ERROR] PROJECT_ROOT tidak valid")
            return

        # ------------------- RESET LOKAL -------------------
        ok, msg = safe_reset_before_pull(base_dir)
        ws.send(f"[RESET] {msg}")
        if not ok:
            ws.send("[ERROR] Reset gagal, update dibatalkan")
            return

        ws.send("[INFO] Memulai git pull...\n")

        # ------------------- PROSES PULL -------------------
        try:
            proc = subprocess.Popen(
                ["git", "pull", "--no-edit"],
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for raw_line in proc.stdout:
                line = raw_line.strip()
                if line:
                    ws.send(line)

            proc.wait()
            code = proc.returncode

            username = session.get("username")

            if code == 0:
                ws.send("[DONE] git pull selesai (exit 0)")
                BMS_write_log(f"Git pull sukses oleh {username}", username)
            else:
                ws.send(f"[ERROR] git pull gagal (exit {code})")
                BMS_write_log(f"Git pull gagal exit {code}", username)

        except Exception as e:
            ws.send(f"[ERROR] Exception saat git pull: {e}")
            BMS_write_log(f"Exception git pull: {e}", session.get("username"))

        ws.send("[END]")

@update.route("/latest-commits")
def latest_commits():
    """
    Ambil 10 commit terbaru dalam format JSON untuk ditampilkan di UI.
    """
    try:
        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            return jsonify({"error": "PROJECT_ROOT tidak valid"}), 500

        # Ambil commit memakai pretty format biar mudah diparsing
        log_cmd = [
            "git", "log", "-10",
            "--pretty=format:%h|%an|%ar|%s"
        ]

        result = subprocess.run(
            log_cmd,
            cwd=base_dir,
            capture_output=True,
            text=True
        )

        commits = []
        for line in result.stdout.splitlines():
            if "|" in line:
                short, author, time, msg = line.split("|", 3)
                commits.append({
                    "hash": short,
                    "author": author,
                    "time": time,
                    "message": msg
                })

        return jsonify({"commits": commits})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

