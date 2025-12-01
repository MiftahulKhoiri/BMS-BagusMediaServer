import os
import zipfile
import shutil
import hashlib
import tarfile
import time
import base64
from flask import Blueprint, request, jsonify, session, send_file, send_from_directory, Response, render_template
from werkzeug.utils import secure_filename

# ROOT dan Auth
from app.BMS_config import BASE
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

# === FIX: blueprint pakai nama fm_premium ===
fm_premium = Blueprint("fm_premium", __name__, url_prefix="/filemanager")

ROOT = BASE
TRASH = os.path.join(ROOT, ".trash")  # Folder untuk recycle bin
SHARE = os.path.join(ROOT, ".share")  # Folder untuk menyimpan link sharing

# Buat folder utama jika belum ada
os.makedirs(ROOT, exist_ok=True)
os.makedirs(TRASH, exist_ok=True)
os.makedirs(SHARE, exist_ok=True)


# ===================================================================
# Helper keamanan
# ===================================================================

def safe(p):
    """
    Memastikan path tetap dalam ROOT directory untuk keamanan
    Mengembalikan ROOT jika path mencoba keluar dari direktori aman
    """
    if not p:
        return ROOT
    real = os.path.abspath(p)
    if not real.startswith(ROOT):
        return ROOT
    return real

def fm_auth():
    """
    Middleware untuk memeriksa otentikasi user
    Mengembalikan error response jika user tidak terautentikasi atau bukan admin/root
    """
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403
    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses ditolak"}), 403
    return None

# ===================================================================
# PREMIUM — ADVANCED SEARCH
# ===================================================================

@fm_premium.route("/search")
def fm_search():
    """
    Pencarian file/folder berdasarkan query
    Mencari secara rekursif dari path yang ditentukan
    Mengembalikan list hasil pencarian dalam format JSON
    """
    check = fm_auth()
    if check: return check

    query = request.args.get("q", "").lower()  # Query pencarian
    start = safe(request.args.get("path") or ROOT)  # Direktori mulai pencarian

    results = []
    # Walk melalui semua direktori dan file
    for root, dirs, files in os.walk(start):
        # Cek file yang sesuai query
        for f in files:
            if query in f.lower():
                results.append(os.path.join(root, f))
        # Cek folder yang sesuai query
        for d in dirs:
            if query in d.lower():
                results.append(os.path.join(root, d))

    return jsonify({"query": query, "results": results})

# ===================================================================
# PREMIUM — FILE INFO DETAIL
# ===================================================================

@fm_premium.route("/info")
def fm_info():
    """
    Mendapatkan informasi detail tentang file/folder
    Termasuk size, waktu created/modified, MD5 hash (untuk file)
    Mengembalikan informasi dalam format JSON
    """
    check = fm_auth()
    if check: return check

    path = safe(request.args.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ditemukan"}), 404

    stat = os.stat(path)
    md5 = ""

    # Hitung MD5 hash hanya untuk file (bukan folder)
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

@fm_premium.route("/edit")
def fm_edit_read():
    """
    Membaca konten file untuk diedit
    Mengembalikan konten file dalam format JSON
    """
    check = fm_auth()
    if check: return check

    path = safe(request.args.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ada"}), 404

    # Baca file dengan encoding UTF-8, ignore errors untuk file binary
    with open(path, "r", encoding="utf8", errors="ignore") as f:
        return jsonify({"content": f.read()})

@fm_premium.route("/edit", methods=["POST"])
def fm_edit_write():
    """
    Menyimpan konten yang diedit ke file
    Menerima path dan content dari form data
    """
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    content = request.form.get("content", "")

    # Tulis konten ke file dengan encoding UTF-8
    with open(path, "w", encoding="utf8") as f:
        f.write(content)

    return jsonify({"status": "saved"})

# ===================================================================
# PREMIUM — TAR/GZIP/RAR/7Z (tanpa rar/7z extractor)
# ===================================================================

@fm_premium.route("/compress", methods=["POST"])
def fm_compress():
    """
    Kompresi file/folder ke format zip, tar, atau gz
    Menerima path file/folder dan mode kompresi
    Mengembalikan path file hasil kompresi
    """
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    mode = request.form.get("mode", "zip")  # zip, tar, gz

    base = os.path.basename(path)
    out = safe(os.path.join(os.path.dirname(path), base + f".{mode}"))

    if mode == "zip":
        # Kompresi ZIP dengan deflate compression
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isfile(path):
                zf.write(path, arcname=base)
            else:
                # Kompresi folder secara rekursif
                for r, d, f in os.walk(path):
                    for x in f:
                        full = os.path.join(r, x)
                        arc = os.path.relpath(full, os.path.dirname(path))
                        zf.write(full, arcname=arc)
    elif mode == "tar":
        # Kompresi TAR tanpa compression
        with tarfile.open(out, "w") as tf:
            tf.add(path, arcname=base)
    elif mode == "gz":
        # Kompresi TAR dengan GZIP compression
        with tarfile.open(out, "w:gz") as tf:
            tf.add(path, arcname=base)

    return jsonify({"status": "ok", "file": out})

@fm_premium.route("/extract", methods=["POST"])
def fm_extract():
    """
    Ekstrak file archive (zip, tar, gz)
    Menerima path file archive dan destination folder
    """
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    dest = safe(request.form.get("dest") or os.path.dirname(path))

    if path.endswith(".zip"):
        # Ekstrak file ZIP
        with zipfile.ZipFile(path) as zf:
            zf.extractall(dest)
    elif path.endswith(".tar") or path.endswith(".gz"):
        # Ekstrak file TAR atau TAR.GZ
        with tarfile.open(path) as tf:
            tf.extractall(dest)

    return jsonify({"status": "ok"})

# ===================================================================
# PREMIUM — RECYCLE BIN (Soft Delete)
# ===================================================================

@fm_premium.route("/delete", methods=["POST"])
def fm_delete_trash():
    """
    Soft delete - Memindahkan file/folder ke recycle bin
    File di-rename dengan timestamp untuk menghindari konflik nama
    """
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    if not os.path.exists(path):
        return jsonify({"error": "Tidak ada"}), 404

    # Tambahkan timestamp untuk menghindari konflik nama
    new = os.path.join(TRASH, f"{int(time.time())}_" + os.path.basename(path))
    shutil.move(path, new)

    return jsonify({"status": "trashed", "trash": new})

@fm_premium.route("/restore", methods=["POST"])
def fm_restore():
    """
    Memulihkan file/folder dari recycle bin
    Menerima path file di trash dan destination untuk restore
    """
    check = fm_auth()
    if check: return check

    src = safe(request.form.get("path"))
    dest = safe(request.form.get("dest") or ROOT)

    shutil.move(src, dest)
    return jsonify({"status": "restored"})

@fm_premium.route("/trash/empty", methods=["POST"])
def fm_empty_trash():
    """
    Mengosongkan recycle bin secara permanen
    Menghapus semua file di folder trash
    """
    check = fm_auth()
    if check: return check

    # Hapus seluruh folder trash dan buat kembali
    shutil.rmtree(TRASH)
    os.makedirs(TRASH, exist_ok=True)
    return jsonify({"status": "trash emptied"})

# ===================================================================
# PREMIUM — PERMISSIONS (chmod + chown)
# ===================================================================

@fm_premium.route("/chmod", methods=["POST"])
def fm_chmod():
    """
    Mengubah permission file/folder (chmod)
    Menerima path dan mode permission dalam format octal
    """
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    mode = int(request.form.get("mode"), 8)  # Convert string octal ke integer
    os.chmod(path, mode)
    return jsonify({"status": "ok"})

@fm_premium.route("/chown", methods=["POST"])
def fm_chown():
    """
    Mengubah ownership file/folder (chown)
    Menerima path, user ID (uid), dan group ID (gid)
    """
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

@fm_premium.route("/share", methods=["POST"])
def fm_share():
    """
    Membuat shareable link untuk file/folder
    Generate token unik dan simpan mapping token-path
    Mengembalikan URL untuk mengakses file
    """
    check = fm_auth()
    if check: return check

    path = safe(request.form.get("path"))
    # Generate token acak yang aman
    token = base64.urlsafe_b64encode(os.urandom(24)).decode()

    # Simpan mapping token ke path asli
    meta = os.path.join(SHARE, token + ".txt")
    with open(meta, "w") as f:
        f.write(path)

    return jsonify({"url": f"/filemanager/share/{token}"})


@fm_premium.route("/share/<token>")
def fm_share_download(token):
    """
    Endpoint untuk mengakses file melalui share link
    Menerima token dan mengembalikan file yang sesuai
    """
    meta = os.path.join(SHARE, token + ".txt")
    if not os.path.exists(meta):
        return "Invalid link", 404

    # Baca path asli dari file meta
    with open(meta) as f:
        path = safe(f.read().strip())

    # Kirim file menggunakan send_file Flask
    return send_file(path)

# ===================================================================
# PREMIUM — STREAMING VIDEO/AUDIO
# ===================================================================

@fm_premium.route("/stream")
def fm_stream():
    """
    Streaming file video/audio
    Menggunakan generator untuk chunked response
    Mendukung seek/range requests secara basic
    """
    check = fm_auth()
    if check: return check

    path = safe(request.args.get("path"))

    def generate():
        """
        Generator untuk membaca file dalam chunks
        Memungkinkan streaming file besar tanpa load memory berlebihan
        """
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 512):  # Baca 512KB per chunk
                yield chunk

    return Response(generate(), mimetype="video/mp4")

# ===================================================================
#  PREMIUM CHUNK UPLOAD (FINAL OPTIMAL VERSION)
# ===================================================================

# Storage folder internal khusus upload
UPLOAD_INTERNAL = ".uploads"
BACKUP_INTERNAL = ".backups"

# Dictionary untuk melacak upload sessions
upload_sessions = {}
upload_lock = Lock()

# SAFE untuk internal folder
def safe_internal(*paths):
    base = os.path.join(ROOT, *paths)
    real = os.path.abspath(base)
    # pastikan tetap di ROOT
    if not real.startswith(ROOT):
        real = ROOT
    return real


# ===================================================================
# START UPLOAD
# ===================================================================
@fm_premium.route("/upload_chunk/start", methods=["POST"])
def fm_chunk_start():
    check = fm_auth()
    if check: return check

    filename = secure_filename(request.form.get("name"))
    file_size = int(request.form.get("total_size", 0))
    file_md5 = request.form.get("file_md5", "")

    # Batas 1GB
    MAX_SIZE = 1 * 1024 * 1024 * 1024
    if file_size > MAX_SIZE:
        return jsonify({"error": "Max file size 1GB"}), 400

    # Session ID unik
    session_id = str(uuid.uuid4())

    # Path temp internal
    temp_filename = f"{session_id}_{filename}.part"
    temp_path = safe_internal(UPLOAD_INTERNAL, temp_filename)

    # Buat direktori internal
    os.makedirs(safe_internal(UPLOAD_INTERNAL), exist_ok=True)

    # Init session tracking
    with upload_lock:
        upload_sessions[session_id] = {
            "filename": filename,
            "temp_path": temp_path,
            "file_size": file_size,
            "uploaded_size": 0,
            "chunk_count": 0,
            "file_md5": file_md5,
            "start_time": time.time(),
            "last_update": time.time(),
            "user_id": session.get("user_id", "unknown")
        }

    # Create empty temp file
    open(temp_path, "wb").close()

    return jsonify({
        "session_id": session_id,
        "temp": temp_filename,
        "recommended_chunk_size": 1024 * 1024  # 1MB
    })


# ===================================================================
# APPEND CHUNK
# ===================================================================
@fm_premium.route("/upload_chunk/append", methods=["POST"])
def fm_chunk_append():
    check = fm_auth()
    if check: return check

    session_id = request.form.get("session_id")
    chunk_index = int(request.form.get("chunk_index", 0))

    if not session_id or session_id not in upload_sessions:
        return jsonify({"error": "Session invalid"}), 400

    session_data = upload_sessions[session_id]
    temp_path = session_data["temp_path"]

    chunk = request.files.get("chunk")
    if not chunk:
        return jsonify({"error": "Chunk missing"}), 400

    chunk_data = chunk.read()
    chunk_size = len(chunk_data)

    # VALIDASI INDEX
    expected_index = session_data["chunk_count"]
    if chunk_index != expected_index:
        return jsonify({
            "error": "Chunk index mismatch",
            "expected": expected_index,
            "got": chunk_index
        }), 409

    # VALIDASI SIZE
    new_total_size = session_data["uploaded_size"] + chunk_size
    if new_total_size > session_data["file_size"]:
        return jsonify({"error": "File size exceeded"}), 400

    # Write chunk
    try:
        with open(temp_path, "ab", buffering=1048576) as f:  # 1MB buffer
            f.write(chunk_data)

    except IOError as e:
        return jsonify({"error": f"Write error: {str(e)}"}), 500

    # Update session
    with upload_lock:
        session_data["uploaded_size"] = new_total_size
        session_data["chunk_count"] += 1
        session_data["last_update"] = time.time()

    progress = (new_total_size / session_data["file_size"]) * 100

    return jsonify({
        "status": "ok",
        "progress": round(progress, 2),
        "uploaded_size": new_total_size,
        "chunk_index": chunk_index
    })


# ===================================================================
# FINISH UPLOAD
# ===================================================================
@fm_premium.route("/upload_chunk/finish", methods=["POST"])
def fm_chunk_finish():
    check = fm_auth()
    if check: return check

    session_id = request.form.get("session_id")
    final_filename = secure_filename(request.form.get("final_filename"))

    if not session_id or session_id not in upload_sessions:
        return jsonify({"error": "Session invalid"}), 400

    session_data = upload_sessions[session_id]
    temp_path = session_data["temp_path"]
    final_path = safe(os.path.join(ROOT, final_filename))

    try:
        # Verifikasi size
        actual_size = os.path.getsize(temp_path)
        if actual_size != session_data["file_size"]:
            return jsonify({"error": "File size mismatch"}), 400

        # Verifikasi MD5 kalau ada
        if session_data["file_md5"]:
            file_hash = hashlib.md5()
            with open(temp_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    file_hash.update(chunk)
            if file_hash.hexdigest() != session_data["file_md5"]:
                return jsonify({"error": "MD5 checksum mismatch"}), 400

        # Handle overwrite → buat folder backup
        os.makedirs(safe_internal(BACKUP_INTERNAL), exist_ok=True)

        if os.path.exists(final_path):
            backup_path = safe_internal(
                BACKUP_INTERNAL,
                f"{final_filename}.backup.{int(time.time())}"
            )
            shutil.move(final_path, backup_path)

        # Pindahkan file
        os.rename(temp_path, final_path)

        # Statistik
        upload_time = time.time() - session_data["start_time"]
        speed = session_data["file_size"] / upload_time if upload_time > 0 else 0

        # Hapus session
        with upload_lock:
            del upload_sessions[session_id]

        return jsonify({
            "status": "finished",
            "file": final_path,
            "file_size": actual_size,
            "upload_time": round(upload_time, 2),
            "speed_bytes": round(speed, 2),
            "chunks_processed": session_data["chunk_count"]
        })

    finally:
        # Cleanup temp jika masih ada
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


# ===================================================================
# CANCEL UPLOAD
# ===================================================================
@fm_premium.route("/upload_chunk/cancel", methods=["POST"])
def fm_chunk_cancel():
    check = fm_auth()
    if check: return check

    session_id = request.form.get("session_id")
    if session_id in upload_sessions:
        temp = upload_sessions[session_id]["temp_path"]

        if os.path.exists(temp):
            try:
                os.remove(temp)
            except:
                pass

        with upload_lock:
            del upload_sessions[session_id]

    return jsonify({"status": "cancelled"})


# ===================================================================
# STATUS UPLOAD
# ===================================================================
@fm_premium.route("/upload_chunk/status")
def fm_chunk_status():
    check = fm_auth()
    if check: return check

    session_id = request.args.get("session_id")

    if not session_id or session_id not in upload_sessions:
        return jsonify({"error": "Session not found"}), 404

    d = upload_sessions[session_id]

    return jsonify({
        "filename": d["filename"],
        "uploaded_size": d["uploaded_size"],
        "total_size": d["file_size"],
        "progress": round((d["uploaded_size"] / d["file_size"]) * 100, 2),
        "chunk_count": d["chunk_count"],
        "user_id": d["user_id"],
        "last_update": d["last_update"]
    })


# ===================================================================
# CLEANUP OLD SESSIONS (Optional)
# ===================================================================
def cleanup_stale_uploads():
    now = time.time()
    stale = []

    with upload_lock:
        for sid, data in upload_sessions.items():
            if now - data["last_update"] > 24 * 3600:  # 24 jam
                stale.append(sid)

        for sid in stale:
            temp = upload_sessions[sid]["temp_path"]
            if os.path.exists(temp):
                try: os.remove(temp)
                except: pass
            del upload_sessions[sid]

# ===================================================================
# PREMIUM UI ROUTE
# ===================================================================

@fm_premium.route("/ui")
def fm_ui():
    """
    Menampilkan interface file manager premium
    Mengembalikan template HTML untuk file manager
    """
    check = fm_auth()
    if check: return check

    return render_template("BMS_filemanager.html")


# ROUTES ui upload 

@fm_premium.route("/upload")
def fm_upload_ui():
    check = fm_auth()
    if check: 
        return check

    return render_template("BMS_upload.html")