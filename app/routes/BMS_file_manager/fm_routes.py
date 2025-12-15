from flask import Blueprint, render_template

from .fm_security import fm_auth
from . import fm_actions as act

fm_premium = Blueprint(
    "fm_premium",
    __name__,
    url_prefix="/filemanager"
)


# =====================================================
# SEARCH
# =====================================================
@fm_premium.route("/search")
def search():
    check = fm_auth()
    if check: return check

    return act.action_search()


# =====================================================
# INFO
# =====================================================
@fm_premium.route("/info")
def info():
    check = fm_auth()
    if check: return check

    return act.action_info()


# =====================================================
# EDITOR
# =====================================================
@fm_premium.route("/edit")
def edit_read():
    check = fm_auth()
    if check: return check

    return act.action_edit_read()


@fm_premium.route("/edit", methods=["POST"])
def edit_write():
    check = fm_auth()
    if check: return check

    return act.action_edit_write()


# =====================================================
# COMPRESS / EXTRACT
# =====================================================
@fm_premium.route("/compress", methods=["POST"])
def compress():
    check = fm_auth()
    if check: return check

    return act.action_compress()


@fm_premium.route("/extract", methods=["POST"])
def extract():
    check = fm_auth()
    if check: return check

    return act.action_extract()


# =====================================================
# TRASH
# =====================================================
@fm_premium.route("/delete", methods=["POST"])
def delete():
    check = fm_auth()
    if check: return check

    return act.action_delete()


@fm_premium.route("/restore", methods=["POST"])
def restore():
    check = fm_auth()
    if check: return check

    return act.action_restore()


@fm_premium.route("/trash/empty", methods=["POST"])
def empty_trash():
    check = fm_auth()
    if check: return check

    return act.action_empty_trash()


# =====================================================
# SHARE
# =====================================================
@fm_premium.route("/share", methods=["POST"])
def share():
    check = fm_auth()
    if check: return check

    return act.action_share()


@fm_premium.route("/share/<token>")
def share_download(token):
    return act.action_share_download(token)


# =====================================================
# STREAM
# =====================================================
@fm_premium.route("/stream")
def stream():
    check = fm_auth()
    if check: return check

    return act.action_stream()


# =====================================================
# UI
# =====================================================
@fm_premium.route("/ui")
def ui():
    check = fm_auth()
    if check: return check

    return render_template("BMS_filemanager.html")