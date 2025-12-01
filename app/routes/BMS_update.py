import os
import subprocess
import zipfile
import shutil
import requests
from datetime import datetime
from flask import Blueprint, jsonify, session, render_template, current_app

from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import BASE, BMS_load_version, BMS_save_version


# =========================================================
#  SETUP BLUEPRINT & PATHS
# =========================================================
update = Blueprint("update", __name__, url_prefix="/update")

UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# =========================================================
#  HELPER: CEK HAK AKSES UPDATE
# =========================================================
def BMS_update_required_simple():
    """Cek apakah user boleh update (admin/root)."""
    if not BMS_auth_is_login():
        return False
    return BMS_auth_is_admin() or BMS_auth_is_root()


# =========================================================
#  CEK UPDATE via GitHub API
# =========================================================
GITHUB_API_COMMITS = (
    "https://api.github.com/repos/MiftahulKhoiri/"
    "BMS-BagusMediaServer/commits?per_page=1"
)

def BMS_check_update():
    """Cek commit terbaru GitHub & bandingkan dengan versi lokal."""
    local_info = BMS_load_version()
    local_commit = local_info.get("commit", "local")
    local_version = local_info.get("version", "1.0.0")

    try:
        response = requests.get(GITHUB_API_COMMITS, timeout=5)
        response.raise_for_status()

        data = response.json()[0]
        remote_commit = data["sha"]
        remote_message = data["commit"]["message"]
        remote_date = data["commit"]["author"]["date"]

        update_available = (remote_commit != local_commit)

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
        return {"success": False, "error": str(e), "update_available": False}


@update.route("/check-api")
def check_update_api():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403
    return jsonify(BMS_check_update())


# =========================================================
#  DOWNLOAD ZIP UPDATE TERBARU
# =========================================================
GITHUB_ZIP_URL = (
    "https://github.com/MiftahulKhoiri/"
    "BMS-BagusMediaServer/archive/refs/heads/main.zip"
)

@update.route("/start-download")
def start_download():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403

    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")

    try:
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
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================
#  EXTRACT ZIP KE FOLDER TEMP
# =========================================================
def extract_update_zip():
    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")
    temp_extract = os.path.join(UPDATE_PATH, "TEMP_EXTRACT")

    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)

    os.makedirs(temp_extract, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_extract)

        extracted_root = None
        for name in os.listdir(temp_extract):
            full = os.path.join(temp_extract, name)
            if os.path.isdir(full):
                extracted_root = full
                break

        return True, extracted_root

    except Exception as e:
        return False, str(e)


# =========================================================
#  BACKUP VERSI LAMA
# =========================================================
def backup_current_version():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_PATH, f"BMS_backup_{timestamp}.zip")

    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            for root, dirs, files in os.walk(BASE):

                if "UPDATE" in root or "BACKUP" in root:
                    continue  # Hindari backup folder update/backup

                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, BASE)
                    backup_zip.write(filepath, arcname)

        return True, backup_file

    except Exception as e:
        return False, str(e)


# =========================================================
#  REPLACE FILE PROJECT DENGAN FILE BARU
# =========================================================
def replace_with_new_version(extracted_root):
    try:
        for root, dirs, files in os.walk(extracted_root):

            rel_path = os.path.relpath(root, extracted_root)
            target_dir = os.path.join(BASE, rel_path)

            os.makedirs(target_dir, exist_ok=True)

            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(target_dir, file)
                shutil.copy2(src, dst)

        return True, "Replace selesai"

    except Exception as e:
        return False, str(e)


# =========================================================
#  APPLY UPDATE (EXTRACT → BACKUP → REPLACE → UPDATE VERSION)
# =========================================================
@update.route("/apply-update")
def apply_update():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403

    # Extract
    ok, result = extract_update_zip()
    if not ok:
        return jsonify({"success": False, "step": "extract", "error": result})
    extracted_root = result

    # Backup
    ok, backup_file = backup_current_version()
    if not ok:
        return jsonify({"success": False, "step": "backup", "error": backup_file})

    # Replace
    ok, msg = replace_with_new_version(extracted_root)
    if not ok:
        return jsonify({"success": False, "step": "replace", "error": msg})

    # Update version.json
    remote_commit = BMS_check_update()["remote_commit"]
    BMS_save_version("1.0.0", remote_commit)

    return jsonify({
        "success": True,
        "message": "Update berhasil diterapkan!",
        "backup_file": backup_file,
        "new_commit": remote_commit
    })


# =========================================================
#  TAMBAHAN: UI Route, Git Updater Lama, Log Commit Lama
# =========================================================
@update.route("/ui")
def BMS_update_ui():
    if not BMS_update_required_simple():
        return jsonify({"error": "Akses ditolak"}), 403
    return render_template("BMS_update.html")


@update.route("/check-update")
def check_update():
    """Mode lama: cek via git local (git pull)."""
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
        return jsonify({"update_available": False, "error": str(e)}), 500


def safe_reset_before_pull(base_dir):
    try:
        subprocess.run(["git", "restore", "."], cwd=base_dir, check=False)
        subprocess.run(["git", "clean", "-fd"], cwd=base_dir, check=False)
        return True, "Reset lokal selesai"
    except Exception as e:
        return False, str(e)


def register_ws(sock):

    @sock.route("/ws/update")
    def ws_update(ws):

        if not BMS_update_required_simple():
            ws.send("[ERROR] Tidak punya izin update (admin/root saja)")
            return

        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            ws.send("[ERROR] PROJECT_ROOT tidak valid")
            return

        ok, msg = safe_reset_before_pull(base_dir)
        ws.send(f"[RESET] {msg}")
        if not ok:
            ws.send("[ERROR] Reset gagal, update dibatalkan")
            return

        ws.send("[INFO] Memulai git pull...\n")

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
            BMS_write_log(f"Exception git pull: {e}", username)

        ws.send("[END]")


@update.route("/latest-commits")
def latest_commits():
    try:
        base_dir = current_app.config.get("PROJECT_ROOT", None)
        if not base_dir or not os.path.isdir(base_dir):
            return jsonify({"error": "PROJECT_ROOT tidak valid"}), 500

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