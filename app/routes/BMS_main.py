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

    @app.main("/")
    def BMS_home():

        if "user_id" not in session:
            return render_template("BMS_welcome.html")

        role = session.get("role", "user")

        if role in ("root", "admin"):
            return redirect("/admin/home")

        return redirect("/user/home")