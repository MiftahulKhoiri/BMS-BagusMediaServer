from flask import Blueprint, redirect
from app.routes.BMS_auth import (
    BMS_auth_has_users,
    BMS_auth_is_login,
    BMS_auth_is_root,
    BMS_auth_is_admin
)

main = Blueprint("main", __name__)


# ===============================
#  HALAMAN UTAMA ("/")
# ===============================

@main.route("/")
def BMS_main_home():

    # 1. Jika belum ada user sama sekali → langsung ke Register ROOT
    if not BMS_auth_has_users():
        return redirect("/auth/register")

    # 2. Jika user sudah login → arahkan sesuai role
    if BMS_auth_is_login():

        # ROOT → Dash Admin
        if BMS_auth_is_root() or BMS_auth_is_admin():
            return redirect("/admin/dashboard")

        # USER → Dashboard User
        return redirect("/user/home")

    # 3. Jika belum login → arahkan ke Login
    return redirect("/auth/login")