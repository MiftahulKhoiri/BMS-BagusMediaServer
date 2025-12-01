import os
import zipfile
import shutil
import hashlib
import tarfile
import time
import base64
from flask import Blueprint, request, jsonify, session, send_file, send_from_directory, Response
from werkzeug.utils import secure_filename

# ROOT dan Auth
from app.BMS_config import BASE
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

fm = Blueprint("fm_premium", __name__, url_prefix="/filemanager")

ROOT = BASE
TRASH = os.path.join(ROOT, ".trash")
SHARE = os.path.join(ROOT, ".share")

os.makedirs(ROOT, exist_ok=True)
os.makedirs(TRASH, exist_ok=True)
os.makedirs(SHARE, exist_ok=True)

# ===================================================================
# Helper keamanan
# ===================================================================

def safe(p):
    if not p:
        return ROOT
    real = os.path.abspath(p)
    if not real.startswith(ROOT):
        return ROOT
    return real

def fm_auth():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses ditolak"}), 403
    return None

# ===================================================================
# PREMIUM — ADVANCED SEARCH
# ===================================================================

@fm.route("/search")
def fm_search():
    check = fm_auth()
    if check: return check

    query = request.args.get("q", "").lower()
    start = safe(request.args.get("path") or ROOT)

    results = []
    for root, dirs, files in os.walk(start):
        for f in files:
            if query in f.lower():
                results.append(os.path.join(root, f))
        for d in dirs:
            if query in d.lower():
                results.append(os.path.join(root, d))

    return jsonify({"query": query, "results": results})

# ===================================================================
# PREMIUM — FILE INFO DETAIL
# ===================================================================

@fm.route("/info")
def fm_info():
    check = fm_auth()
    if check: return check

    path = safe(request.args.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ditemukan"}), 404

    stat = os.stat(path)
    md5 = ""

    if os.path.isfile(path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        md5 = h.hexdigest()

    info = {
        "name": os.path.basename(path),
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "md5": md5,
        "is_dir": os.path.isdir(path)
    }

    return jsonify(info)

# ===================================================================
# PREMIUM — EDITOR (Read & Save)
# ===================================================================

@fm.route("/edit")
def fm_edit_read():
    check = fm_auth()
    if check: return check

    path = safe(request.args.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ada"}), 404

    with open(path, "r", encoding="utf8", errors="ignore") as f:
        return jsonify({"content": f.read()})

@fm.route("/edit", methods=["POST"])
def fm_edit_write():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    content = request.form.get("content", "")

    with open(path, "w", encoding="utf8") as f:
        f.write(content)

    return jsonify({"status": "saved"})

# ===================================================================
# PREMIUM — TAR/GZIP/RAR/7Z (tanpa rar/7z extractor)
# ===================================================================

@fm.route("/compress", methods=["POST"])
def fm_compress():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    mode = request.form.get("mode", "zip")  # zip, tar, gz

    base = os.path.basename(path)
    out = safe(os.path.join(os.path.dirname(path), base + f".{mode}"))

    if mode == "zip":
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isfile(path):
                zf.write(path, arcname=base)
            else:
                for r, d, f in os.walk(path):
                    for x in f:
                        full = os.path.join(r, x)
                        arc = os.path.relpath(full, os.path.dirname(path))
                        zf.write(full, arcname=arc)
    elif mode == "tar":
        with tarfile.open(out, "w") as tf:
            tf.add(path, arcname=base)
    elif mode == "gz":
        with tarfile.open(out, "w:gz") as tf:
            tf.add(path, arcname=base)

    return jsonify({"status": "ok", "file": out})

@fm.route("/extract", methods=["POST"])
def fm_extract():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    dest = safe(request.form.get("dest") or os.path.dirname(path))

    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            zf.extractall(dest)
    elif path.endswith(".tar") or path.endswith(".gz"):
        with tarfile.open(path) as tf:
            tf.extractall(dest)

    return jsonify({"status": "ok"})

# ===================================================================
# PREMIUM — RECYCLE BIN (Soft Delete)
# ===================================================================

@fm.route("/delete", methods=["POST"])
def fm_delete_trash():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ada"}), 404

    new = os.path.join(TRASH, f"{int(time.time())}_" + os.path.basename(path))
    shutil.move(path, new)

    return jsonify({"status": "trashed", "trash": new})

@fm.route("/restore", methods=["POST"])
def fm_restore():
    check = fm_auth()
    if check: return check

    src = safe(request.form.get("path"))
    dest = safe(request.form.get("dest") or ROOT)

    shutil.move(src, dest)
    return jsonify({"status": "restored"})

@fm.route("/trash/empty", methods=["POST"])
def fm_empty_trash():
    check = fm_auth()
    if check: return check

    shutil.rmtree(TRASH)
    os.makedirs(TRASH, exist_ok=True)
    return jsonify({"status": "trash emptied"})

# ===================================================================
# PREMIUM — PERMISSIONS (chmod + chown)
# ===================================================================

@fm.route("/chmod", methods=["POST"])
def fm_chmod():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    mode = int(request.form.get("mode"), 8)
    os.chmod(path, mode)
    return jsonify({"status": "ok"})

@fm.route("/chown", methods=["POST"])
def fm_chown():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    uid = int(request.form.get("uid"))
    gid = int(request.form.get("gid"))

    os.chown(path, uid, gid)
    return jsonify({"status": "ok"})

# ===================================================================
# PREMIUM — SHARE LINK (Token)
# ===================================================================

@fm.route("/share", methods=["POST"])
def fm_share():
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    token = base64.urlsafe_b64encode(os.urandom(24)).decode()

    meta = os.path.join(SHARE, token + ".txt")
    with open(meta, "w") as f:
        f.write(path)

    return jsonify({"url": f"/filemanager/share/{token}"})


@fm.route("/share/<token>")
def fm_share_download(token):
    meta = os.path.join(SHARE, token + ".txt")
    if not os.path.exists(meta):
        return "Invalid link", 404

    with open(meta) as f:
        path = safe(f.read().strip())

    return send_file(path)

# ===================================================================
# PREMIUM — STREAMING VIDEO/AUDIO
# ===================================================================

@fm.route("/stream")
def fm_stream():
    check = fm_auth()
    if check: return check

    path = safe(request.args.get("path"))

    def generate():
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 512):
                yield chunk

    return Response(generate(), mimetype="video/mp4")

# ===================================================================
# PREMIUM — CHUNK UPLOAD (1GB Aman)
# ===================================================================

@fm.route("/upload_chunk/start", methods=["POST"])
def fm_chunk_start():
    check = fm_auth()
    if check: return check

    filename = secure_filename(request.form.get("name"))
    temp = safe(os.path.join(ROOT, filename + ".part"))
    open(temp, "wb").close()
    return jsonify({"temp": temp})

@fm.route("/upload_chunk/append", methods=["POST"])
def fm_chunk_append():
    check = fm_auth()
    if check: return check

    temp = safe(request.form.get("temp"))
    chunk = request.files["chunk"]

    with open(temp, "ab") as f:
        f.write(chunk.read())

    return jsonify({"status": "ok"})

@fm.route("/upload_chunk/finish", methods=["POST"])
def fm_chunk_finish():
    check = fm_auth()
    if check: return check

    temp = safe(request.form.get("temp"))
    final = safe(request.form.get("final"))

    os.rename(temp, final)
    return jsonify({"status": "finished", "file": final})

from flask import render_template

@fm.route("/ui")
def fm_ui():
    check = fm_auth()
    if check: return check

    return render_template("BMS_filemanager.html")