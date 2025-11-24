import os
from flask import Blueprint, render_template, request, redirect, session
from jinja2 import TemplateNotFound
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
#   📄 AJAX Loader Halaman Admin (aman)
# ======================================================
@admin.route("/page")
def BMS_admin_page_loader():
    check = BMS_admin_required()
    if check:
        return check

    page = request.args.get("name")
    username = session.get("username")

    # Cegah path kosong
    if not page:
        BMS_write_log("Halaman admin diminta tanpa parameter", username)
        return "<p>❌ Parameter halaman kosong.</p>"

    # Cegah path traversal
    if ".." in page or "/" in page or "\\" in page:
        BMS_write_log(f"Percobaan akses ilegal: {page}", username)
        return "<p>❌ Akses ilegal.</p>"

    BMS_write_log(f"Admin membuka halaman: {page}", username)

    html_file = f"{page}.html"

    try:
        return render_template(html_file)

    except TemplateNotFound:
        BMS_write_log(f"Halaman tidak ditemukan: {page}", username)
        return "<p>❌ Halaman tidak ditemukan.</p>"