import os
from flask import Blueprint, render_template, request, redirect, session
from jinja2 import TemplateNotFound
from app.routes.BMS_auth import (
    BMS_auth_is_login,
)
from app.routes.BMS_logger import BMS_write_log

user = Blueprint("user", __name__, url_prefix="/user")


# ======================================================
#   🔐 Proteksi User
# ======================================================
def BMS_user_required():
    if not BMS_auth_is_login():
        BMS_write_log("Akses ditolak (belum login)", "UNKNOWN")
        return redirect("/auth/login")
    return None


# ======================================================
#   🏠 Halaman Home User
# ======================================================
@user.route("/home")
def BMS_user_home():
    check = BMS_user_required()
    if check:
        return check

    username = session.get("username")
    BMS_write_log("Akses halaman user home", username)

    return render_template("BMSuser_home.html")


# ======================================================
#   📄 AJAX Loader Halaman User (AMAN)
# ======================================================
@user.route("/page")
def BMS_user_page_loader():
    check = BMS_user_required()
    if check:
        return check

    page = request.args.get("name")
    username = session.get("username")

    # INVALID: jika tidak ada parameter
    if not page:
        BMS_write_log("Halaman user kosong diminta", username)
        return "<p>❌ Parameter halaman kosong.</p>"

    # BLOKIR path traversal
    if ".." in page or "/" in page or "\\" in page:
        BMS_write_log(f"Percobaan akses ilegal user: {page}", username)
        return "<p>❌ Akses ilegal.</p>"

    BMS_write_log(f"Membuka halaman user: {page}", username)

    html_file = f"{page}.html"

    try:
        return render_template(html_file)
    except TemplateNotFound:
        return "<p>❌ Halaman tidak ditemukan.</p>"