from flask import Blueprint, render_template, request, jsonify
from .BMS_utils import require_root
from app.BMS_config import (
    DB_PATH, PROFILE_FOLDER, MUSIC_FOLDER,
    VIDEO_FOLDER, UPLOAD_FOLDER
)
import sqlite3
import os
import shutil

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ============================================================
#  DATABASE HANDLER
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
#  ADMIN HOME
# ============================================================
@admin.route("/home")
def BMS_admin_home():
    cek = require_root()
    if cek:
        return cek

    try:
        conn = get_db()
        users = conn.execute(
            "SELECT id, username, role FROM users"
        ).fetchall()
        conn.close()
    except Exception as e:
        return f"Database error: {str(e)}", 500

    return render_template("BMSadmin_home.html", users=users)


# ============================================================
#  USER MANAGER PAGE
# ============================================================
@admin.route("/user-list")
def BMS_user_list_page():
    cek = require_root()
    if cek:
        return cek
    return render_template("BMS_user_list.html")


# ============================================================
#  API: LIST USER
# ============================================================
@admin.route("/users/list")
def admin_user_list():
    cek = require_root()
    if cek:
        return cek

    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, username, role FROM users"
        ).fetchall()
        conn.close()
    except Exception as e:
        return jsonify({"error": "DB error", "detail": str(e)}), 500

    users = [
        {"id": r["id"], "username": r["username"], "role": r["role"]}
        for r in rows
    ]
    return jsonify({"users": users})


# ============================================================
#  API: UPDATE ROLE
# ============================================================
@admin.route("/users/update-role", methods=["POST"])
def admin_update_role():
    cek = require_root()
    if cek:
        return cek

    data = request.json or {}
    user_id = data.get("id")
    role = data.get("role")

    # Validasi input
    if not user_id or not role:
        return jsonify({"status": "error", "message": "Data tidak lengkap."}), 400

    try:
        conn = get_db()
        conn.execute(
            "UPDATE users SET role=? WHERE id=?",
            (role, user_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success", "message": "Role user berhasil diubah."})


# ============================================================
#  API: DELETE USER + FILES
# ============================================================
@admin.route("/users/delete", methods=["DELETE"])
def admin_delete_user():
    cek = require_root()
    if cek:
        return cek

    data = request.json or {}
    user_id = data.get("id")

    if not user_id:
        return jsonify({"status": "error", "message": "User ID tidak diberikan."}), 400

    try:
        conn = get_db()

        # Hapus log user (jika ada)
        try:
            conn.execute("DELETE FROM logs WHERE user_id=?", (user_id,))
        except:
            pass

        # Hapus user
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

        # Hapus folder user (profile, music, video)
        folder_paths = [
            os.path.join(PROFILE_FOLDER, str(user_id)),
            os.path.join(MUSIC_FOLDER, str(user_id)),
            os.path.join(VIDEO_FOLDER, str(user_id)),
            os.path.join(UPLOAD_FOLDER, str(user_id))
        ]

        for folder in folder_paths:
            if os.path.exists(folder):
                shutil.rmtree(folder)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success", "message": "User & semua datanya berhasil dihapus."})