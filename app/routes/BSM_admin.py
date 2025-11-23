from flask import Blueprint, render_template, session, request

admin = Blueprint("admin", __name__, url_prefix="/admin")

def BMS_admin_is_root():
    return session.get("role") == "root"

@admin.route("/dashboard")
def BMS_admin_dashboard():
    if not BMS_admin_is_root():
        return "Akses ditolak!"
    return render_template("BMSadmin_dashboard.html")


# Loader AJAX untuk panel kanan
@admin.route("/page")
def BMS_admin_load_page():
    page = request.args.get("name")

    if page == "home":
        return "<h2>Home Panel</h2><p>Selamat datang di panel admin BMS.</p>"

    if page == "tools":
        return "<h2>Tools</h2><p>Update • Install • Restart • Shutdown</p>"

    if page == "filemanager":
        return "<h2>File Manager</h2><p>UI File Manager akan disini.</p>"

    if page == "mp3":
        return "<h2>MP3 Player</h2><p>Player akan disini.</p>"

    if page == "video":
        return "<h2>Video Player</h2><p>Player video akan disini.</p>"

    if page == "users":
        return "<h2>Users</h2><p>Daftar user & management nanti disini.</p>"

    return "<p>Halaman tidak ditemukan.</p>"