from flask import Blueprint, render_template
from .BMS_utils import require_login

user = Blueprint("user", __name__, url_prefix="/user")


@user.route("/home")
def BMS_user_home():
    cek = require_login()
    if cek:
        return cek

    return render_template("BMSuser_home.html")