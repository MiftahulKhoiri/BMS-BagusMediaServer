import sqlite3
import os
from flask import Blueprint, render_template, request, jsonify, session, redirect

# 🔗 Import konfigurasi & helper
from app.BMS_config import DB_PATH

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ======================================================
#   📌 Helper: Koneksi Database
# ======================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================
#   🔐 Cek akses admin
# ======================================================
def require_root():
    if session.get("role") != "root":
        return redirect("/auth/login")
    return None


# ======================================================
#   🧾 Daftar Semua User
# ======================================================
@admin.route("/users")
def admin_users():
    cek = require_root()
    if cek:
        return cek

    conn = get_db()
    users = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()

    return render_template("BMS_user_list.html", users=users)


# ======================================================
#   🆕 Tambah User Baru
# ======================================================
@admin.route("/add_user", methods=["POST"])
def admin_add_user():
    cek = require_root()
    if cek:
        return cek

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "user")

    if not username or not password:
        return jsonify({"status": "error", "message": "Semua kolom wajib diisi!"})

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "User berhasil ditambahkan!"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username sudah ada!"})
    finally:
        conn.close()


# ======================================================
#   🗑️ Hapus User
# ======================================================
@admin.route("/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    cek = require_root()
    if cek:
        return cek

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "User dihapus."})


# ======================================================
#   🛠️ Ubah Role User
# ======================================================
@admin.route("/update_role/<int:user_id>", methods=["POST"])
def admin_update_role(user_id):
    cek = require_root()
    if cek:
        return cek

    new_role = request.form.get("role", "user")

    conn = get_db()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Role user diperbarui."})


# ======================================================
#   ⚙️ Reset Database User (opsi berisiko)
# ======================================================
@admin.route("/reset_users", methods=["POST"])
def admin_reset_users():
    cek = require_root()
    if cek:
        return cek

    conn = get_db()
    conn.execute("DELETE FROM users WHERE role != 'root'")
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Semua user non-root dihapus."})


# ======================================================
#   📊 Statistik User
# ======================================================
@admin.route("/stats")
def admin_stats():
    cek = require_root()
    if cek:
        return cek

    conn = get_db()
    users = conn.execute("SELECT role, COUNT(*) as jumlah FROM users GROUP BY role").fetchall()
    conn.close()

    return render_template("BMS_admin_home.html", users=users)