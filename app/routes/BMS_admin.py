import os
from flask import Blueprint, render_template, request, redirect, session
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)
from app.routes.BMS_logger import BMS_write_log

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ======================================================
#   🔐 Proteksi: hanya ADMIN & ROOT
# ======================================================
def BMS_admin_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses admin ditolak (belum login)", "UNKNOWN")
        return redirect("/auth/login")

    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        BMS_write_log("Akses admin ditolak (tanpa izin)", session.get("username"))
        return "❌ Akses ditolak! Hanya ADMIN / ROOT!"

    return None


# ======================================================
#   🏠 Dashboard Admin
# ======================================================
@admin.route("/dashboard")
def BMS_admin_dashboard():
    check = BMS_admin_required()
    if check:
        return check

    user = session.get("username")
    BMS_write_log("Akses dashboard admin", user)

    return render_template("BMSadmin_home.html")


# ======================================================
#   📄 AJAX Loader Halaman Admin
# ======================================================
@admin.route("/page")
def BMS_admin_page_loader():
    check = BMS_admin_required()
    if check:
        return check

    page = request.args.get("name")
    username = session.get("username")

    BMS_write_log(f"Admin membuka halaman: {page}", username)

    # Konversi -> nama file HTML
    html_file = f"{page}.html"

    # Pastikan file ada
    template_path = os.path.join("app", "templates", html_file)
    if not os.path.exists(template_path):
        BMS_write_log(f"Halaman tidak ditemukan: {page}", username)
        return "<p>❌ Halaman tidak ditemukan.</p>"

    return render_template(html_file)