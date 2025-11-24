from flask import Blueprint, render_template, request, redirect
from app.routes.BMS_auth import (
    BMS_auth_is_login,
)

user = Blueprint("user", __name__, url_prefix="/user")


# ======================================================
#   🔐 Proteksi Halaman User
# ======================================================
def BMS_user_required():
    """Cek apakah user sudah login."""
    if not BMS_auth_is_login():
        return redirect("/auth/login")
    return None


# ======================================================
#   🏠 Dashboard User
# ======================================================
@user.route("/home")
def BMS_user_home():
    check = BMS_user_required()
    if check:
        return check

    return render_template("BMSuser_home.html")


# ======================================================
#   📄 AJAX Loader langsung ambil file dari templates/
# ======================================================
@user.route("/page")
def BMS_user_page_loader():
    """
    Contoh pemanggilan:
    /user/page?name=BMS_mp3
    /user/page?name=BMS_video
    /user/page?name=BMS_upload
    /user/page?name=BMS_profile

    Maka akan load:
    app/templates/<name>.html
    """
    check = BMS_user_required()
    if check:
        return check

    page = request.args.get("name")

    try:
        return render_template(f"{page}.html")
    except:
        return "❌ Halaman user tidak ditemukan."