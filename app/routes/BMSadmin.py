from flask import Blueprint, render_template, session, redirect

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.route("/home")
def BMS_admin_home():
    if session.get("role") != "root":
        return "Akses ditolak! Hanya ROOT yang boleh masuk!"

    return render_template("BMSadmin_home.html")