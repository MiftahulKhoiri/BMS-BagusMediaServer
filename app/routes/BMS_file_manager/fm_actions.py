import os
import zipfile
import tarfile
import shutil
import hashlib
import time
import base64
import mimetypes
from flask import request, jsonify, Response, send_file

from .fm_security import safe, ROOT, TRASH, SHARE


# =====================================================
# INFO FILE / FOLDER
# =====================================================
def action_info():
    path = safe(request.args.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ditemukan"}), 404

    stat = os.stat(path)
    md5 = None

    if os.path.isfile(path):
        try:
            h = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            md5 = h.hexdigest()
        except:
            pass

    return jsonify({
        "name": os.path.basename(path),
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "md5": md5,
        "is_dir": os.path.isdir(path)
    })


# =====================================================
# EDITOR
# =====================================================
def action_edit_read():
    path = safe(request.args.get("path"))
    if not os.path.isfile(path):
        return jsonify({"error": "Tidak bisa dibaca"}), 404

    with open(path, "r", encoding="utf8", errors="ignore") as f:
        return jsonify({"content": f.read()})


def action_edit_write():
    path = safe(request.form.get("path"))
    content = request.form.get("content", "")

    try:
        with open(path, "w", encoding="utf8") as f:
            f.write(content)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "saved"})


# =====================================================
# COMPRESS
# =====================================================
def action_compress():
    path = safe(request.form.get("path"))
    mode = request.form.get("mode", "zip")

    base = os.path.basename(path)
    out = safe(os.path.join(os.path.dirname(path), base + f".{mode}"))

    try:
        if mode == "zip":
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.isfile(path):
                    zf.write(path, arcname=base)
                else:
                    for r, _, files in os.walk(path):
                        for f in files:
                            full = os.path.join(r, f)
                            arc = os.path.relpath(full, os.path.dirname(path))
                            zf.write(full, arcname=arc)

        elif mode == "tar":
            with tarfile.open(out, "w") as tf:
                tf.add(path, arcname=base)

        elif mode == "gz":
            with tarfile.open(out, "w:gz") as tf:
                tf.add(path, arcname=base)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok", "file": out})


# =====================================================
# EXTRACT
# =====================================================
def action_extract():
    path = safe(request.form.get("path"))
    dest = safe(request.form.get("dest") or os.path.dirname(path))

    try:
        if path.endswith(".zip"):
            with zipfile.ZipFile(path) as zf:
                for m in zf.namelist():
                    if ".." in m:
                        return jsonify({"error": "Zip slip blocked"}), 400
                zf.extractall(dest)

        elif path.endswith(".tar") or path.endswith(".gz"):
            with tarfile.open(path) as tf:
                tf.extractall(dest)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok"})


# =====================================================
# TRASH
# =====================================================
def action_delete():
    path = safe(request.form.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ada"}), 404

    new = os.path.join(TRASH, f"{int(time.time())}_" + os.path.basename(path))
    shutil.move(path, new)

    return jsonify({"status": "trashed", "trash": new})


def action_restore():
    src = safe(request.form.get("path"))
    dest = safe(request.form.get("dest") or ROOT)

    shutil.move(src, dest)
    return jsonify({"status": "restored"})


def action_empty_trash():
    shutil.rmtree(TRASH, ignore_errors=True)
    os.makedirs(TRASH, exist_ok=True)
    return jsonify({"status": "trash emptied"})


# =====================================================
# SHARE LINK
# =====================================================
def action_share():
    path = safe(request.form.get("path"))
    if not os.path.isfile(path):
        return jsonify({"error": "Hanya file"}), 400

    token = base64.urlsafe_b64encode(os.urandom(24)).decode()
    meta = os.path.join(SHARE, token + ".txt")

    with open(meta, "w") as f:
        f.write(path)

    return jsonify({"url": f"/filemanager/share/{token}"})


def action_share_download(token):
    meta = os.path.join(SHARE, token + ".txt")
    if not os.path.exists(meta):
        return "Invalid link", 404

    with open(meta) as f:
        path = safe(f.read().strip())

    return send_file(path)


# =====================================================
# STREAM
# =====================================================
def action_stream():
    path = safe(request.args.get("path"))
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"

    def generate():
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 512)
                if not chunk:
                    break
                yield chunk

    return Response(generate(), mimetype=mime)