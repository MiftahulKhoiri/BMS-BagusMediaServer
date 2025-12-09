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


update = Blueprint("update", __name__, url_prefix="/update")

UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")

os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)


# =========================================================
#  HELPER: Validasi Hak Akses Update
# =========================================================
def BMS_update_required():
    if not BMS_auth_is_login():
        return False
    return BMS_auth_is_admin() or BMS_auth_is_root()


# =========================================================
#  CHECK UPDATE ONLINE via GitHub API
# =========================================================
GITHUB_API_COMMITS = (
    "https://api.github.com/repos/MiftahulKhoiri/"
    "BMS-BagusMediaServer/commits?per_page=1"
)

def BMS_check_update():
    local_info = BMS_load_version()
    local_commit = local_info.get("commit", None)
    local_version = local_info.get("version", "1.0.0")

    try:
        r = requests.get(GITHUB_API_COMMITS, timeout=5)
        r.raise_for_status()

        data = r.json()[0]
        remote_commit = data["sha"]

        return {
            "success": True,
            "local_commit": local_commit,
            "local_version": local_version,
            "remote_commit": remote_commit,
            "update_available": (remote_commit != local_commit)
        }

    except Exception as e:
        return {"success": False, "error": str(e), "update_available": False}


@update.route("/check-api")
def check_update_api():
    if not BMS_update_required():
        return jsonify({"error": "Akses ditolak"}), 403
    return jsonify(BMS_check_update())


# =========================================================
#  DOWNLOAD ZIP UPDATE
# =========================================================
GITHUB_ZIP_URL = (
    "https://github.com/MiftahulKhoiri/"
    "BMS-BagusMediaServer/archive/refs/heads/main.zip"
)

@update.route("/start-download")
def start_download():
    if not BMS_update_required():
        return jsonify({"error": "Tidak ada izin"}), 403

    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")

    try:
        r = requests.get(GITHUB_ZIP_URL, stream=True, timeout=10)
        r.raise_for_status()

        with open(zip_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

        BMS_write_log("Download update ZIP sukses", session.get("username"))
        return jsonify({"success": True, "zip_path": zip_path})

    except Exception as e:
        BMS_write_log(f"Download update gagal: {e}", "SYSTEM")
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================
#  ZIP EXTRACTION (ANTI ZIP-SLIP)
# =========================================================
def safe_extract(zip_path, extract_to):
    """
    Anti ZIP SLIP — memastikan tidak keluar folder tujuan.
    """
    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.infolist():

            # skip version.json (config kamu tetap digunakan)
            if member.filename.endswith("version.json"):
                continue

            # normalize path
            target = os.path.realpath(os.path.join(extract_to, member.filename))
            if not target.startswith(os.path.realpath(extract_to)):
                raise Exception("ZIP Slip attempt blocked")

            z.extract(member, extract_to)


def extract_update_zip():
    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")
    temp_extract = os.path.join(UPDATE_PATH, "TEMP_EXTRACT")

    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)

    os.makedirs(temp_extract, exist_ok=True)

    try:
        safe_extract(zip_path, temp_extract)

        # cari folder root hasil extract
        dirs = [os.path.join(temp_extract, d) for d in os.listdir(temp_extract)]
        dirs = [d for d in dirs if os.path.isdir(d)]
        if not dirs:
            return False, "Gagal mendeteksi folder extract"

        return True, dirs[0]

    except Exception as e:
        return False, str(e)


# =========================================================
#  BACKUP CURRENT VERSION (AMAN)
# =========================================================
PROTECTED_FOLDERS = {
    "database",
    "uploads",
    "upload",
    "music",
    "video",
    "profile",
    "logs",
}

PROTECTED_FILES = {
    "version.json",
    ".env",
    "config.json",
}

def backup_current_version():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_PATH, f"backup_{timestamp}.zip")

    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as z:

            for root, dirs, files in os.walk(BASE):
                rel = os.path.relpath(root, BASE)

                # skip folder besar/user data
                if rel.split(os.sep)[0] in PROTECTED_FOLDERS:
                    continue

                for file in files:
                    if file in PROTECTED_FILES:
                        continue
                    z.write(os.path.join(root, file),
                            arcname=os.path.join(rel, file))

        return True, backup_file

    except Exception as e:
        return False, str(e)


# =========================================================
#  SAFE REPLACE FILES
# =========================================================
def replace_with_new(extracted_root):
    try:
        for root, dirs, files in os.walk(extracted_root):

            rel = os.path.relpath(root, extracted_root)
            if rel.split(os.sep)[0] in PROTECTED_FOLDERS:
                continue

            dst_dir = os.path.join(BASE, rel)
            os.makedirs(dst_dir, exist_ok=True)

            for file in files:
                if file in PROTECTED_FILES:
                    continue
                src = os.path.join(root, file)
                dst = os.path.join(dst_dir, file)
                shutil.copy2(src, dst)

        return True, "Replace completed"
    except Exception as e:
        return False, str(e)


# =========================================================
#  ROLLBACK jika update gagal
# =========================================================
def rollback(backup_zip):
    try:
        temp_restore = os.path.join(UPDATE_PATH, "TEMP_RESTORE")

        if os.path.exists(temp_restore):
            shutil.rmtree(temp_restore)

        os.makedirs(temp_restore, exist_ok=True)

        with zipfile.ZipFile(backup_zip, 'r') as z:
            z.extractall(temp_restore)

        # overwrite kembali
        for root, dirs, files in os.walk(temp_restore):
            rel = os.path.relpath(root, temp_restore)
            dst = os.path.join(BASE, rel)
            os.makedirs(dst, exist_ok=True)

            for f in files:
                if f in PROTECTED_FILES:
                    continue
                shutil.copy2(os.path.join(root, f),
                             os.path.join(dst, f))

        return True, "Rollback berhasil"

    except Exception as e:
        return False, str(e)


# =========================================================
#  APPLY UPDATE
# =========================================================
@update.route("/apply-update")
def apply_update():
    if not BMS_update_required():
        return jsonify({"error": "Tidak ada izin"}), 403

    # extract
    ok, result = extract_update_zip()
    if not ok:
        return jsonify({"success": False, "step": "extract", "error": result})

    extracted_root = result

    # backup lama
    ok, backup_file = backup_current_version()
    if not ok:
        return jsonify({"success": False, "step": "backup", "error": backup_file})

    # replace
    ok, msg = replace_with_new(extracted_root)
    if not ok:
        rollback(backup_file)
        return jsonify({
            "success": False,
            "step": "replace",
            "error": msg,
            "rollback": "Rollback berhasil"
        })

    # update versi.json
    update_info = BMS_check_update()
    if update_info["success"]:
        BMS_save_version("1.0.0", update_info["remote_commit"])

    return jsonify({"success": True, "message": "Update berhasil!"})


@update.route("/ui")
def update_ui():
    if not BMS_update_required():
        return jsonify({"error": "Tidak ada izin"}), 403
    return render_template("BMS_update.html")