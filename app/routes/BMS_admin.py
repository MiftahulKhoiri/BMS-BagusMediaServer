from flask import Blueprint, render_template
from .BMS_utils import require_root
from app.BMS_config import DB_PATH
import sqlite3

admin = Blueprint("admin", __name__, url_prefix="/admin")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@admin.route("/home")
def BMS_admin_home():
    cek = require_root()
    if cek:
        return cek

    conn = get_db()

    # Statistik pengguna
    total_user = conn.execute("SELECT COUNT(*) AS jml FROM users").fetchone()["jml"]
    total_admin = conn.execute("SELECT COUNT(*) AS jml FROM users WHERE role='admin'").fetchone()["jml"]
    total_user_biasa = conn.execute("SELECT COUNT(*) AS jml FROM users WHERE role='user'").fetchone()["jml"]

    # LIST USER (WAJIB BIAR TABEL MUNCUL)
    users = conn.execute("SELECT id, username, role FROM users").fetchall()

    conn.close()

    return render_template(
        "BMSadmin_home.html",
        total_user=total_user,
        total_admin=total_admin,
        total_user_biasa=total_user_biasa,
        users=users
    )

@admin.route("/delete/<int:user_id>")
def delete_user(user_id):
    cek = require_root()
    if cek:
        return cek

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/home")