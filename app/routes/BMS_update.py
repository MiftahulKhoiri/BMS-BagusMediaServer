import os
import requests
import zipfile
import shutil
import time
from datetime import datetime
from threading import Lock
from flask import Blueprint, jsonify, session, render_template

from app.routes.BMS_auth.session_helpers import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log, BMS_write_error
from app.BMS_config import BASE, BMS_load_version, BMS_save_version

# Blueprint
update = Blueprint("update", __name__, url_prefix="/update")

# Paths
UPDATE_PATH = os.path.join(BASE, "UPDATE")
BACKUP_PATH = os.path.join(BASE, "BACKUP")
os.makedirs(UPDATE_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)

# Protected items (won't be overwritten)
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

# GitHub endpoints (ke folder repo milikmu)
GITHUB_API_COMMITS = (
    "https://api.github.com/repos/MiftahulKhoiri/"
    "BMS-BagusMediaServer/commits?per_page=1"
)
GITHUB_ZIP_URL = (
    "https://github.com/MiftahulKhoiri/"
    "BMS-BagusMediaServer/archive/refs/heads/main.zip"
)

# Download / extraction limits
MAX_DOWNLOAD_SIZE = 200 * 1024 * 1024   # 200 MB
MAX_EXTRACT_TOTAL = 500 * 1024 * 1024   # 500 MB aggregate uncompressed

# Websocket clients (simple broadcast)
_WS_CLIENTS = []
_ws_lock = Lock()


# =========================================================
#  AUTH/ACCESS
# =========================================================
def BMS_update_required():
    if not BMS_auth_is_login():
        return False
    return BMS_auth_is_admin() or BMS_auth_is_root()


# =========================================================
#  CHECK UPDATE ONLINE via GitHub API
# =========================================================
def BMS_check_update():
    local_info = BMS_load_version()
    local_commit = local_info.get("commit", None)
    local_version = local_info.get("version", "1.0.0")

    try:
        r = requests.get(GITHUB_API_COMMITS, timeout=6)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or not data:
            raise Exception("Invalid response from GitHub API")

        remote_commit = data[0].get("sha")
        if not remote_commit:
            raise Exception("No commit sha found")

        return {
            "success": True,
            "local_commit": local_commit,
            "local_version": local_version,
            "remote_commit": remote_commit,
            "update_available": (remote_commit != local_commit)
        }

    except Exception as e:
        BMS_write_error(f"Gagal cek update: {e}", "SYSTEM")
        return {"success": False, "error": str(e), "update_available": False}


@update.route("/check-api")
def check_update_api():
    if not BMS_update_required():
        return jsonify({"error": "Akses ditolak"}), 403
    return jsonify(BMS_check_update())


# =========================================================
#  SAFE STREAM DOWNLOAD (chunked, size limit)
# =========================================================
def download_file_stream(url, dest_path, max_bytes=MAX_DOWNLOAD_SIZE, timeout=15):
    """
    Download file secara streaming; batasi total bytes agar tidak kehabisan disk/memory.
    """
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise Exception("File terlalu besar, hentikan download")
                    f.write(chunk)
        return True, dest_path
    except Exception as e:
        return False, str(e)


@update.route("/start-download")
def start_download():
    if not BMS_update_required():
        return jsonify({"error": "Tidak ada izin"}), 403

    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")

    try:
        ok, result = download_file_stream(GITHUB_ZIP_URL, zip_path)
        if not ok:
            BMS_write_error(f"Download update gagal: {result}", "SYSTEM")
            return jsonify({"success": False, "error": result}), 500

        BMS_write_log("Download update ZIP sukses", session.get("username"))
        broadcast_update({"type": "download_complete", "path": zip_path})
        return jsonify({"success": True, "zip_path": zip_path})

    except Exception as e:
        BMS_write_error(f"Download update exception: {e}", "SYSTEM")
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================
#  ZIP EXTRACTION (ANTI ZIP-SLIP + SIZE LIMIT)
# =========================================================
def safe_extract(zip_path, extract_to, max_total=MAX_EXTRACT_TOTAL):
    """
    Anti ZIP SLIP & limit total uncompressed size to avoid zip-bomb.
    Returns list of extracted file paths.
    """
    extracted_files = []
    total_uncompressed = 0

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():

            # skip version.json supaya versi lokal tetap dikontrol
            if member.filename.endswith("version.json"):
                continue

            # normalize path
            member_path = member.filename
            target = os.path.realpath(os.path.join(extract_to, member_path))

            if not target.startswith(os.path.realpath(extract_to)):
                raise Exception("ZIP Slip attempt blocked")

            # estimate size (prefer member.file_size)
            total_uncompressed += member.file_size
            if total_uncompressed > max_total:
                raise Exception("Total ukuran extract terlalu besar (possible zip bomb)")

            # create target folder then extract single member
            parent = os.path.dirname(target)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)

            # actually extract member to the target path
            with z.open(member) as source, open(target, "wb") as dest:
                shutil.copyfileobj(source, dest)

            extracted_files.append(target)

    return extracted_files


def extract_update_zip():
    zip_path = os.path.join(UPDATE_PATH, "update_latest.zip")
    temp_extract = os.path.join(UPDATE_PATH, "TEMP_EXTRACT")

    # cleanup
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)
    os.makedirs(temp_extract, exist_ok=True)

    if not os.path.exists(zip_path):
        return False, "File ZIP tidak ditemukan"

    try:
        files = safe_extract(zip_path, temp_extract)
        # detect root folder inside extract (repo archive usually has single root)
        root_entries = [d for d in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, d))]
        if not root_entries:
            return False, "Gagal mendeteksi folder extract"
        extracted_root = os.path.join(temp_extract, root_entries[0])
        return True, extracted_root
    except Exception as e:
        BMS_write_error(f"Extract failed: {e}", "SYSTEM")
        return False, str(e)


# =========================================================
#  BACKUP CURRENT VERSION (AMAN)
# =========================================================
def backup_current_version():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_PATH, f"backup_{timestamp}.zip")

    try:
        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(BASE):
                rel = os.path.relpath(root, BASE)
                first_part = rel.split(os.sep)[0] if rel and rel != "." else ""

                # skip folder besar/user data
                if first_part in PROTECTED_FOLDERS:
                    continue

                for file in files:
                    if file in PROTECTED_FILES:
                        continue
                    full = os.path.join(root, file)
                    arcname = os.path.join(rel, file) if rel and rel != "." else file
                    z.write(full, arcname=arcname)

        return True, backup_file

    except Exception as e:
        BMS_write_error(f"Backup failed: {e}", "SYSTEM")
        return False, str(e)


# =========================================================
#  SAFE REPLACE FILES
# =========================================================
def replace_with_new(extracted_root):
    try:
        for root, dirs, files in os.walk(extracted_root):
            rel = os.path.relpath(root, extracted_root)
            first_part = rel.split(os.sep)[0] if rel and rel != "." else ""

            if first_part in PROTECTED_FOLDERS:
                continue

            dst_dir = os.path.join(BASE, rel) if rel and rel != "." else BASE
            os.makedirs(dst_dir, exist_ok=True)

            for file in files:
                if file in PROTECTED_FILES:
                    continue
                src = os.path.join(root, file)
                dst = os.path.join(dst_dir, file)
                shutil.copy2(src, dst)

        return True, "Replace completed"
    except Exception as e:
        BMS_write_error(f"Replace failed: {e}", "SYSTEM")
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

        with zipfile.ZipFile(backup_zip, "r") as z:
            z.extractall(temp_restore)

        # overwrite kembali (skip protected files)
        for root, dirs, files in os.walk(temp_restore):
            rel = os.path.relpath(root, temp_restore)
            dst = os.path.join(BASE, rel) if rel and rel != "." else BASE
            os.makedirs(dst, exist_ok=True)

            for f in files:
                if f in PROTECTED_FILES:
                    continue
                shutil.copy2(os.path.join(root, f), os.path.join(dst, f))

        BMS_write_log("Rollback berhasil", "SYSTEM")
        broadcast_update({"type": "rollback", "file": backup_zip})
        return True, "Rollback berhasil"

    except Exception as e:
        BMS_write_error(f"Rollback failed: {e}", "SYSTEM")
        return False, str(e)


# =========================================================
#  APPLY UPDATE (endpoint)
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
        # rollback
        rb_ok, rb_msg = rollback(backup_file)
        return jsonify({
            "success": False,
            "step": "replace",
            "error": msg,
            "rollback": rb_msg if rb_ok else "Rollback gagal"
        })

    # update version.json (simpan commit)
    update_info = BMS_check_update()
    if update_info.get("success"):
        try:
            BMS_save_version(update_info.get("local_version", "1.0.0"), update_info.get("remote_commit"))
        except Exception:
            # avoid failing the whole operation if version save has minor issue
            BMS_write_error("Gagal menyimpan version.json setelah update", "SYSTEM")

    BMS_write_log("Update applied successfully", session.get("username"))
    broadcast_update({"type": "update_applied"})
    return jsonify({"success": True, "message": "Update berhasil!"})


@update.route("/ui")
def update_ui():
    if not BMS_update_required():
        return jsonify({"error": "Tidak ada izin"}), 403
    return render_template("BMS_update.html")


# =========================================================
#  WEBSOCKET: simple broadcast support
#  register_ws(sock) akan dipanggil di create_app (kamu mengirim Sock object)
# =========================================================
def register_ws(sock):
    """
    Register sebuah route websocket untuk broadcasting.
    Gunakan Sock dari flask_sock.
    """
    try:
        @sock.route("/update/ws")
        def _ws(ws):
            # Simpel: tambahkan client ke list lalu dengarkan
            with _ws_lock:
                _WS_CLIENTS.append(ws)
            BMS_write_log("WebSocket client connected", "SYSTEM")

            try:
                # Loop menerima pesan (tetap hidup) — jika client kirim pesan, kita log
                while True:
                    msg = ws.receive()
                    if msg is None:
                        break
                    # hanya log pesan inbound (client -> server)
                    BMS_write_log(f"WS recv: {msg}", "SYSTEM")
            except Exception as e:
                # ignore, connection likely closed
                BMS_write_error(f"WS connection error: {e}", "SYSTEM")
            finally:
                with _ws_lock:
                    if ws in _WS_CLIENTS:
                        _WS_CLIENTS.remove(ws)
                BMS_write_log("WebSocket client disconnected", "SYSTEM")

        BMS_write_log("WebSocket route '/update/ws' registered", "SYSTEM")
        return True

    except Exception as e:
        BMS_write_error(f"Failed to register ws: {e}", "SYSTEM")
        return False


def broadcast_update(payload):
    """
    Broadcast payload (dict) as stringified message to all connected websocket clients.
    Non-blocking best-effort send.
    """
    import json
    msg = json.dumps(payload)
    with _ws_lock:
        clients = list(_WS_CLIENTS)
    for ws in clients:
        try:
            ws.send(msg)
        except Exception as e:
            BMS_write_error(f"Failed to send WS message: {e}", "SYSTEM")
            # cleanup dead client
            with _ws_lock:
                if ws in _WS_CLIENTS:
                    _WS_CLIENTS.remove(ws)