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

media_mp3 = Blueprint("media_mp3", __name__, url_prefix="/mp3")


# ============================================================================
#   LIST FOLDERS
# ============================================================================
@media_mp3.route("/folders")
def list_folders():
    owner = current_user_identifier()
    conn = get_db()

    rows = conn.execute("""
        SELECT f.id, f.folder_name,
               (SELECT COUNT(*) FROM mp3_tracks t
                WHERE t.folder_id = f.id AND t.user_id = ?) AS total_mp3
        FROM mp3_folders f
        WHERE (SELECT COUNT(*) FROM mp3_tracks t WHERE t.folder_id = f.id AND t.user_id = ?) > 0
        ORDER BY f.folder_name ASC
    """, (owner, owner)).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================================
#   LIST TRACKS BY FOLDER
# ============================================================================
@media_mp3.route("/folder/<int:folder_id>/tracks")
def folder_tracks(folder_id):
    owner = current_user_identifier()
    conn = get_db()

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
    owner = current_user_identifier()
    conn = get_db()

    row = conn.execute("""
        SELECT id, filename, filepath, size, is_favorite, play_count
        FROM mp3_tracks WHERE id=? AND user_id=?
    """, (track_id, owner)).fetchone()

    conn.close()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    return jsonify(dict(row))


# ============================================================================
#   TOGGLE FAVORITE
# ============================================================================
@media_mp3.route("/favorite/<int:track_id>", methods=["POST"])
def toggle_favorite(track_id):
    owner = current_user_identifier()
    conn = get_db()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT is_favorite FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, owner)).fetchone()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    new_state = 0 if row["is_favorite"] else 1

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
    """Range Header Processing"""
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
    owner = current_user_identifier()
    conn = get_db()

    row = conn.execute("""
        SELECT filepath FROM mp3_tracks
        WHERE id=? AND user_id=?
    """, (track_id, owner)).fetchone()

    conn.close()

    if not row:
        return jsonify({"error": "Track tidak ditemukan"}), 404

    fp = row["filepath"]

    # Increment play count
    try:
        conn = get_db()
        conn.execute("UPDATE mp3_tracks SET play_count = play_count + 1 WHERE id=? AND user_id=?", (track_id, owner))
        conn.commit()
        conn.close()
    except:
        pass

    # Range streaming
    r = parse_range_header(fp)
    if r:
        start, end, size = r
        length = end - start + 1

        with open(fp, "rb") as f:
            f.seek(start)
            data = f.read(length)

        resp = Response(data, 206, mimetype="audio/mpeg")
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(length))
        return resp

    # normal streaming
    return send_file(fp, mimetype="audio/mpeg")


# ============================================================================
#   PLAYER PAGES
# ============================================================================
@media_mp3.route("/")
def home():
    return render_template("BMS_mp3.html")


@media_mp3.route("/watch/<int:track_id>")
def watch(track_id):
    return render_template("BMS_mp3_play.html")