# ============================================================================
# BMS_video_routes.py — Routes untuk UI & API list/play/delete (owner-scoped)
# - No forced login on page view (page accessible)
# - List endpoints filtered by owner
# ============================================================================

from flask import Blueprint, jsonify, render_template, request, Response
from .BMS_video_db import get_db, current_user_identifier, is_inside_video_folder
import os

# Membuat Blueprint untuk rute video dengan prefix '/video'
video_routes = Blueprint("video_routes", __name__, url_prefix="/video")


@video_routes.route("/")
def page_video():
    """
    Menampilkan halaman utama video player.
    
    Halaman ini dapat diakses tanpa memaksa login, tetapi frontend mungkin
    akan meminta pengguna untuk login jika diperlukan (misalnya untuk akses ke video pribadi).
    
    Returns:
        Rendered template: Halaman utama video player (BMS_video.html)
    """
    return render_template("BMS_video.html")


@video_routes.route("/folders")
def list_folders():
    """
    Mengembalikan daftar folder video yang dimiliki oleh user saat ini.
    
    Setiap folder yang dikembalikan hanya jika dimiliki oleh user yang sedang login/guest.
    Response dalam format JSON yang berisi informasi folder beserta jumlah video di dalamnya.
    
    Returns:
        JSON array: Daftar folder dengan id, nama folder, path folder, dan jumlah video
    """
    owner = current_user_identifier()
    conn = get_db()
    
    # Query untuk mengambil folder milik user beserta jumlah video di dalamnya
    rows = conn.execute("""
        SELECT id, folder_name, folder_path,
               (SELECT COUNT(*) FROM videos v
                WHERE v.folder_id = folders.id AND v.user_id=?)
               AS total_video
        FROM folders
        WHERE user_id=?
        ORDER BY folder_name ASC
    """, (owner, owner)).fetchall()
    
    conn.close()
    return jsonify([dict(r) for r in rows])


@video_routes.route("/folder/<int:folder_id>/videos")
def list_videos(folder_id):
    """
    Mengembalikan daftar video dalam folder tertentu yang dimiliki oleh user saat ini.
    
    Args:
        folder_id (int): ID folder yang ingin dilihat video-videonya
    
    Returns:
        JSON array: Daftar video dengan id, nama file, path file, ukuran, dan waktu penambahan
    """
    owner = current_user_identifier()
    conn = get_db()
    
    # Query untuk mengambil semua video dalam folder tertentu milik user
    rows = conn.execute("""
        SELECT id, filename, filepath, size, added_at
        FROM videos
        WHERE folder_id=? AND user_id=?
        ORDER BY filename ASC
    """, (folder_id, owner)).fetchall()
    
    conn.close()
    return jsonify([dict(r) for r in rows])


@video_routes.route("/play/<int:video_id>")
def play_video(video_id):
    """
    Stream video dengan dukungan Range header untuk seek/partial content.
    
    Video hanya dapat diakses jika dimiliki oleh user yang sedang login/guest.
    Fungsi ini mendukung HTTP Range requests untuk pemutaran yang efisien.
    
    Args:
        video_id (int): ID video yang akan diputar
    
    Returns:
        Response: File video lengkap atau sebagian (206 Partial Content) dengan headers yang sesuai
    """
    owner = current_user_identifier()
    conn = get_db()

    # Query untuk mengambil informasi video berdasarkan ID dan kepemilikan user
    row = conn.execute("""
        SELECT filepath, user_id
        FROM videos
        WHERE id=? AND user_id=?
    """, (video_id, owner)).fetchone()

    conn.close()

    # Jika video tidak ditemukan, kembalikan error 404
    if not row:
        return "Video tidak ditemukan", 404

    # Ambil filepath asli (menghapus suffix "::user::" jika ada)
    fp = row["filepath"].split("::user::")[0]

    # Validasi keberadaan file fisik
    if not os.path.exists(fp):
        return "File fisik hilang", 404

    # Ambil ukuran file untuk perhitungan Range
    size = os.path.getsize(fp)
    range_header = request.headers.get("Range")

    # Jika tidak ada Range header, kembalikan seluruh file
    if not range_header:
        return Response(open(fp, "rb").read(), mimetype="video/mp4")

    # Proses Range header untuk partial content (seek)
    parts = range_header.replace("bytes=", "").split("-")
    start = int(parts[0]) if parts[0] else 0
    end = int(parts[1]) if len(parts) > 1 and parts[1] else size - 1
    length = end - start + 1

    # Baca bagian file yang diminta
    with open(fp, "rb") as f:
        f.seek(start)
        data = f.read(length)

    # Buat response dengan status 206 (Partial Content)
    resp = Response(data, 206, mimetype="video/mp4")
    resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
    resp.headers.add("Accept-Ranges", "bytes")
    resp.headers.add("Content-Length", str(length))
    return resp


@video_routes.route("/watch/<int:video_id>")
def video_watch(video_id):
    """
    Menampilkan halaman pemutaran untuk video tertentu.
    
    Video hanya dapat ditonton jika dimiliki oleh user yang sedang login/guest.
    Halaman ini akan menampilkan video player untuk video yang dipilih.
    
    Args:
        video_id (int): ID video yang akan diputar di halaman ini
    
    Returns:
        Rendered template: Halaman pemutaran video dengan player (BMS_video_play.html)
    """
    owner = current_user_identifier()
    conn = get_db()

    # Query untuk mengambil informasi video berdasarkan ID dan kepemilikan user
    row = conn.execute("""
        SELECT id, filename, folder_id, filepath, user_id
        FROM videos
        WHERE id=? AND user_id=?
    """, (video_id, owner)).fetchone()

    conn.close()

    # Jika video tidak ditemukan, kembalikan error 404
    if not row:
        return "Video tidak ditemukan / akses ditolak", 404

    # Kirim informasi video ke template untuk ditampilkan
    return render_template(
        "BMS_video_play.html",
        video_id=row["id"],
        filename=row["filename"],
        folder_id=row["folder_id"]
    )