from flask import Blueprint, render_template, session, redirect
from app.routes.BMS_auth import (
    BMS_auth_is_login,
    BMS_auth_is_member,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

user = Blueprint("user", __name__, url_prefix="/user")


# ===============================
#  Proteksi Halaman User
# ===============================

def BMS_user_required():
    """User, Admin dan Root boleh masuk"""
    if not BMS_auth_is_login():
        return redirect("/auth/login")
    return None


# ===============================
#  DASHBOARD USER
# ===============================

@user.route("/home")
def BMS_user_home():
    check = BMS_user_required()
    if check:
        return check

    username = session.get("username")
    role = session.get("role")

    return f"""
    <h2>👤 User Dashboard</h2>
    <p>Halo <b>{username}</b>!</p>
    <p>Role kamu: <b>{role}</b></p>
    <a href='/auth/logout'>Logout</a>
    """