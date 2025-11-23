from flask import Blueprint, render_template, session, request, redirect
from app.routes.BMS_auth import (
    BMS_auth_is_root,
    BMS_auth_is_admin,
    BMS_auth_is_login
)

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ===============================
#  Proteksi Halaman Admin
# ===============================

def BMS_admin_required():
    """Root dan Admin boleh masuk"""
    if not BMS_auth_is_login():
        return redirect("/auth/login")

    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return "Akses ditolak! Khusus ROOT atau ADMIN!"
    return None


# ===============================
#  DASHBOARD ADMIN
# ===============================

@admin.route("/dashboard")
def BMS_admin_dashboard():
    # cek proteksi
    check = BMS_admin_required()
    if check:
        return check

    return render_template("BMSadmin_dashboard.html")


# ===============================
#  LOADER HALAMAN AJAX
# ===============================

@admin.route("/page")
def BMS_admin_load_page():
    # cek proteksi
    check = BMS_admin_required()
    if check:
        return check

    page = request.args.get("name")

    # HALAMAN HOME
    if page == "home":
        return """
        <h2>🏠 Admin Home</h2>
        <p>Selamat datang di BMS Admin Panel.</p>
        """

    # HALAMAN TOOLS
    if page == "tools":
        return """
        <h2>🛠 Tools</h2>
        <button onclick="fetch('/tools/update').then(r=>r.text()).then(alert)">Update Server</button>
        <br><br>
        <button onclick="fetch('/tools/restart').then(r=>r.text()).then(alert)">Restart Server</button>
        <br><br>
        <button onclick="fetch('/tools/shutdown').then(r=>r.text()).then(alert)">Shutdown Server</button>
        """

    # HALAMAN FILE MANAGER
    if page == "filemanager":
        return "<h2>📁 File Manager</h2><p>UI File Manager akan muncul di sini.</p>"

    # HALAMAN MP3
    if page == "mp3":
        return "<h2>🎵 MP3 Player</h2><iframe src='/mp3/player' width='100%' height='400px'></iframe>"

    # HALAMAN VIDEO
    if page == "video":
        return "<h2>🎬 Video Player</h2><iframe src='/video/player' width='100%' height='400px'></iframe>"

    # HALAMAN USER MANAGER
    if page == "users":
        return "<h2>👤 User Manager</h2><p>Manajemen user akan dibuat di sini.</p>"

    return "<p>Halaman tidak ditemukan.</p>"