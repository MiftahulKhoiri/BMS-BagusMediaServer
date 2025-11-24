import os
from flask import Blueprint, render_template, request, redirect, session
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
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
#   📄 AJAX Loader Halaman User (Modern)
# ======================================================
@user.route("/page")
def BMS_user_page_loader():
    check = BMS_user_required()
    if check:
        return check

    page = request.args.get("name")
    username = session.get("username")

    # Catat akses halaman
    BMS_write_log(f"Membuka halaman user: {page}", username)

    # Muat file HTML sesuai nama
    html_file = f"{page}.html"

    template_path = os.path.join("app", "templates", html_file)
    if not os.path.exists(template_path):
        return "<p>Halaman tidak ditemukan!</p>"

    return render_template(html_file)