from flask import Blueprint, render_template, request, jsonify, redirect
from .BMS_utils import require_root
from app.BMS_config import DB_PATH
import sqlite3
import shutil
import os

admin = Blueprint("admin", __name__, url_prefix="/admin")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@admin.route("/home")
def BMS_admin_home():
    # cek hak akses root
    cek = require_root()
    if cek:
        return cek

    conn = get_db()

    # Ambil semua user — kita tidak lagi mengirim statistik terpisah
    users = conn.execute("SELECT id, username, role FROM users").fetchall()

    conn.close()

    # Kirim hanya users ke template. Jika template mau menampilkan jumlah,
    # bisa gunakan {{ users|length }} di Jinja.
    return render_template(
        "BMSadmin_home.html",
        users=users
    )


# HALAMAN USER MANAGER
@admin.route("/user-list")
def BMS_user_list_page():
    cek = require_root()
    if cek:
        return cek

    return render_template("BMS_user_list.html")


# API LIST USER (dipakai oleh user-list.js)
@admin.route("/users/list")
def admin_user_list():
    cek = require_root()
    if cek:
        return cek

    conn = get_db()
    rows = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()

    users = [
        {"id": r["id"], "username": r["username"], "role": r["role"]}
        for r in rows
    ]

    return jsonify({"users": users})


# UPDATE ROLE
@admin.route("/users/update-role", methods=["POST"])
def admin_update_role():
    cek = require_root()
    if cek:
        return cek

    data = request.json
    user_id = data.get("id")
    role = data.get("role")

    conn = get_db()
    conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Role user berhasil diubah."})


# DELETE USER + DATA
@admin.route("/users/delete", methods=["DELETE"])
def admin_delete_user():
    cek = require_root()
    if cek:
        return cek

    data = request.json
    user_id = data.get("id")

    conn = get_db()

    # Hapus data terkait (jika ada tabel/ folder)
    try:
        conn.execute("DELETE FROM logs WHERE user_id=?", (user_id,))
    except:
        pass

    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "User & semua data berhasil dihapus."})
