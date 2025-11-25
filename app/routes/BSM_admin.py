from flask import Blueprint, render_template
from .BMS_utils import require_root

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/home")
def BMS_admin_home():
    cek = require_root()
    if cek:
        return cek

    return render_template("BMSadmin_home.html")