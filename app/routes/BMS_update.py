import os
import shutil
import zipfile
import requests
from flask import Blueprint, jsonify, session, render_template

from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log
from app.BMS_config import BASE

update = Blueprint("update", __name__, url_prefix="/update")

# ======================================================
#   CONFIG REPO GITHUB
# ======================================================
GITHUB_REPO = "https://github.com/baguschoiri/BMS-BagusMediaServer/archive/refs/heads/main.zip"

UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# ======================================================
#   🔐 Proteksi Akses Update
# ======================================================
def BMS_update_required():
    """Hanya admin / root yang boleh update"""
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login!"}), 403

    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses update hanya untuk admin/root!"}), 403

    return None


# ======================================================
#   🖥 HALAMAN GUI UPDATE
# ======================================================
@update.route("/ui")
def BMS_update_ui():
    check = BMS_update_required()
    if check:
        return check

    return render_template("BMS_update.html")


# ======================================================
#   🔍 CHECK UPDATE (simulasi)
# ======================================================
@update.route("/check")
def BMS_update_check():
    check = BMS_update_required()
    if check:
        return check

    # Simulasi versi online
    online_version = "1.0.1"
    current_version = "1.0.0"

    return jsonify({
        "current": current_version,
        "online": online_version,
        "update_available": current_version != online_version
    })


# ======================================================
#   🔥 DOWNLOAD FILE ZIP DARI GITHUB
# ======================================================
def download_zip(url, dest):
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        return False

    with open(dest, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    return True


# ======================================================
#   🔥 BACKUP PROJECT SEBELUM UPDATE
# ======================================================
def backup_project():
    backup_dir = os.path.join(BACKUP_PATH, "backup_latest")
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)

    shutil.copytree(
        "/data/data/com.termux/files/home/BMS-BagusMediaServer",
        backup_dir
    )
    return backup_dir


# ======================================================
#   🔥 APPLY UPDATE ZIP KE PROJECT
# ======================================================
def apply_update(zip_file):
    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(UPDATE_PATH)

    # Nama folder hasil extract GitHub
    extracted = os.path.join(
        UPDATE_PATH,
        "BMS-BagusMediaServer-main"
    )

    project_dir = "/data/data/com.termux/files/home/BMS-BagusMediaServer"

    # Timpa file ke project
    for item in os.listdir(extracted):
        src = os.path.join(extracted, item)
        dst = os.path.join(project_dir, item)

        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    return True


# ======================================================
#   🚀 JALANKAN UPDATE OTOMATIS
# ======================================================
@update.route("/do")
def BMS_update_do():
    check = BMS_update_required()
    if check:
        return check

    username = session.get("username")

    # 1️⃣ Backup project lama
    backup_path = backup_project()
    BMS_write_log(f"Backup dibuat di {backup_path}", username)

    # 2️⃣ Download update dari GitHub
    zip_path = os.path.join(UPDATE_PATH, "update.zip")
    ok = download_zip(GITHUB_REPO, zip_path)

    if not ok:
        return jsonify({"error": "Gagal download update GitHub!"}), 500

    BMS_write_log("Update ZIP berhasil di-download", username)

    # 3️⃣ Apply update
    apply_update(zip_path)

    BMS_write_log("Update berhasil diterapkan!", username)

    return jsonify({"status": "ok", "msg": "Update berhasil!"})


# ======================================================
#   📄 LOG UPDATE
# ======================================================
@update.route("/logs")
def BMS_update_logs():
    try:
        log_file = os.path.join(BASE, "logs", "system.log")
        with open(log_file, "r") as f:
            data = f.read()
        return jsonify({"log": data})
    except:
        return jsonify({"log": ""})