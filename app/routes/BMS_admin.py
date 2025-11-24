from flask import Blueprint, render_template, request, redirect
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ======================================================
#   🔐 Proteksi Admin
# ======================================================
def BMS_admin_required():
    """Proteksi akses: hanya ROOT atau ADMIN."""
    if not BMS_auth_is_login():
        return redirect("/auth/login")
    if not (BMS_auth_is_root() or BMS_auth_is_admin()):
        return "❌ Akses ditolak!"
    return None


# ======================================================
#   🏠 Dashboard Admin
# ======================================================
@admin.route("/dashboard")
def BMS_admin_dashboard():
    """
    Halaman utama Admin Panel.
    Menampilkan: BMSadmin_home.html
    """
    check = BMS_admin_required()
    if check:
        return check

    return render_template("BMSadmin_home.html")


# ======================================================
#   📄 Loader Halaman Admin (AJAX)
# ======================================================
@admin.route("/page")
def BMS_admin_load_page():
    """
    Loader dinamis sub-halaman admin.
    Semua file disimpan di:
    templates/admin/<nama>.html
    """
    check = BMS_admin_required()
    if check:
        return check

    page = request.args.get("name")

    try:
        return render_template(f"admin/{page}.html")
    except:
        return "❌ Halaman admin tidak ditemukan."