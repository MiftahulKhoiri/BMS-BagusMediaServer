from functools import wraps
from flask import jsonify

from app.routes.BMS_auth.session_helpers import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

def fm_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if not BMS_auth_is_login():
            return jsonify({"error": "Belum login"}), 403

        if not (BMS_auth_is_admin() or BMS_auth_is_root()):
            return jsonify({"error": "Akses ditolak"}), 403

        return func(*args, **kwargs)

    return wrapper