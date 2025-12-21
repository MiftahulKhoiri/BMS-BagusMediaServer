# ============================================================================
#   BMS MP3 MODULE — MAIN ROUTES (FINAL)
#   Mengatur:
#       ✔ Folder List
#       ✔ Track List
#       ✔ Favorite ❤️
#       ✔ Track Info
#       ✔ Streaming (Range Support)
#       ✔ Player Page
# ============================================================================

import os
from flask import Blueprint, jsonify, request, send_file, Response, render_template
from .BMS_mp3_db import get_db, current_user_identifier

# Membuat Blueprint untuk rute media MP3 dengan prefix '/mp3'
media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")


# ============================================================================
#   LIST FOLDERS
# ============================================================================
@media_mp3.route("/folders")
def list_folders():
    """
    Mengembalikan daftar folder yang berisi MP3 milik user saat ini.
    
    Setiap folder yang dikembalikan hanya jika memiliki setidaknya satu track
    milik user yang sedang login. Response dalam format JSON.
    
    Returns:
        JSON array berisi objek folder dengan id, nama folder, dan jumlah MP3
    """
    # Ambil identifier user yang sedang login
    owner = current_user_identifier()
    conn = get_db()

    # Query untuk mengambil folder beserta jumlah track MP3 di dalamnya
    rows = conn.execute("""
        SELECT f.id, f.folder_name,
               (SELECT COUNT(*) FROM mp3_tracks t
                WHERE t.folder_id = f.id AND t.user_id = ?) AS total_mp3
        FROM mp3_folders f
        WHERE (SELECT COUNT(*) FROM mp3_tracks t WHERE t.folder_id = f.id AND t.user_id = ?) > 0
        ORDER BY f.folder_name ASC
    """, (owner, owner)).fetchall()

    conn.close()
    # Konversi setiap row menjadi dictionary dan kembalikan sebagai JSON array
    return jsonify([dict(r) for r in rows])


# ============================================================================
#   LIST TRACKS BY FOLDER
# ============================================================================
@media_mp3.route("/folder/<int:folder_id>/tracks")
def folder_tracks(folder_id):
    """
    Mengembalikan daftar track MP3 dalam folder tertentu milik user saat ini.
    
    Args:
        folder_id (int): ID folder yang ingin dilihat track-nya
    
    Returns:
        JSON array berisi objek track dengan informasi dasar
    """
    owner = current_user_identifier()
    conn = get_db()

    # Query untuk mengambil semua track dalam folder tertentu milik user
    rows = conn.execute("""
        SELECT id, filename, filepath, size, is_favorite, play_count
        FROM mp3_tracks
        WHERE folder_id=? AND user_id=?
        ORDER BY filename ASC
    """, (folder_id, owner)).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================================
#   GET TRACK INFO
# ============================================================================
@media_mp3.route("/info/<int:track_id>")
def track_info(track_id):
    """
    Mengembalikan informasi detail untuk sebuah track MP3 berdasarkan ID.
    
    Args:
        track_id (int): ID track yang ingin dilihat informasinya
    
    Returns:
        JSON object berisi detail track atau error 404 jika tidak ditemukan
    """
    owner = current_user_identifier()
    conn = get_db()

    # Query untuk mengambil informasi track berdasarkan ID dan kepemilikan user
    row = conn.execute("""
        SELECT id, filename, filepath, size, is_favorite, play_count
        FROM mp3_tracks WHERE id=? AND user_id=?
    """, (track_id, owner)).fetchone()

    conn.close()

    # Jika track tidak ditemukan, kembalikan error 404
    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    # Kembalikan informasi track dalam format JSON
    return jsonify(dict(row))


# ============================================================================
#   TOGGLE FAVORITE
# ============================================================================
@media_mp3.route("/favorite/<int:track_id>", methods=["POST"])
def toggle_favorite(track_id):
    """
    Mengubah status favorit (is_favorite) sebuah track (toggle).
    
    Jika track saat ini adalah favorit (is_favorite=1), maka akan diubah menjadi 0,
    dan sebaliknya. Hanya track milik user yang sedang login yang dapat diubah.
    
    Args:
        track_id (int): ID track yang status favoritnya akan diubah
    
    Returns:
        JSON object berisi status operasi dan nilai is_favorite yang baru
    """
    owner = current_user_identifier()
    conn = get_db()
    cur = conn.cursor()

    # Ambil status favorit saat ini
    row = cur.execute("""
        SELECT is_favorite FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, owner)).fetchone()

    # Jika track tidak ditemukan, kembalikan error 404
    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    # Tentukan nilai baru: 0 jika saat ini 1, dan sebaliknya
    new_state = 0 if row["is_favorite"] else 1

    # Update status favorit di database
    cur.execute("""
        UPDATE mp3_tracks SET is_favorite=?
        WHERE id=? AND user_id=?
    """, (new_state, track_id, owner))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "is_favorite": new_state})


# ============================================================================
#   STREAM MP3 (RANGE SUPPORT)
# ============================================================================
def parse_range_header(path):
    """
    Memproses HTTP Range header untuk mendukung streaming sebagian file.
    
    Args:
        path (str): Path file yang akan distream
    
    Returns:
        tuple: (start, end, size) jika header valid, atau None jika tidak valid
    """
    header = request.headers.get("Range")
    if not header:
        return None

    try:
        unit, rng = header.split("=")
        start_s, end_s = rng.split("-")

        size = os.path.getsize(path)
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else size - 1

        return start, end, size
    except:
        return None


@media_mp3.route("/play/<int:track_id>")
def play(track_id):
    """
    Stream file MP3 dengan dukungan Range header untuk seek/partial content.
    
    Fungsi ini juga menambah jumlah pemutaran (play_count) setiap kali track diputar.
    
    Args:
        track_id (int): ID track yang akan diputar
    
    Returns:
        Response: File MP3 lengkap atau sebagian (206 Partial Content) dengan headers yang sesuai
    """
    owner = current_user_identifier()
    conn = get_db()

    # Ambil path file track berdasarkan ID dan kepemilikan user
    row = conn.execute("""
        SELECT filepath FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, owner)).fetchone()

    conn.close()

    # Jika track tidak ditemukan, kembalikan error 404
    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    fp = row["filepath"]

    # Tingkatkan jumlah pemutaran (play_count) track ini
    try:
        conn = get_db()
        conn.execute("UPDATE mp3_tracks SET play_count = play_count + 1 WHERE id=? AND user_id=?", (track_id, owner))
        conn.commit()
        conn.close()
    except:
        pass  # Jika gagal menambah play_count, lanjutkan streaming

    # Proses Range header untuk partial content (seek)
    r = parse_range_header(fp)
    if r:
        start, end, size = r
        length = end - start + 1

        # Baca bagian file yang diminta
        with open(fp, "rb") as f:
            f.seek(start)
            data = f.read(length)

        # Buat response dengan status 206 (Partial Content)
        resp = Response(data, 206, mimetype="audio/mpeg")
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(length))
        return resp

    # Jika tidak ada Range header, kembalikan seluruh file
    return send_file(fp, mimetype="audio/mpeg")


# ============================================================================
#   PLAYER PAGES
# ============================================================================
@media_mp3.route("/")
def home():
    """
    Menampilkan halaman utama player MP3.
    
    Returns:
        Rendered template: Halaman player MP3
    """
    return render_template("BMS_mp3.html")


@media_mp3.route("/watch/<int:track_id>")
def watch(track_id):
    """
    Menampilkan halaman pemutaran untuk track tertentu.
    
    Args:
        track_id (int): ID track yang akan diputar di halaman ini
    
    Returns:
        Rendered template: Halaman pemutaran track dengan player
    """
    return render_template("BMS_mp3_play_modelB.html")