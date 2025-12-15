import os
from flask import jsonify

from app.BMS_config import BASE
from app.routes.BMS_auth.session_helpers import (
    BMS_auth_is_login,
    BMS_auth_is_admin,
    BMS_auth_is_root
)

# ROOT DIRECTORY
ROOT = BASE
TRASH = os.path.join(ROOT, ".trash")
SHARE = os.path.join(ROOT, ".share")

os.makedirs(ROOT, exist_ok=True)
os.makedirs(TRASH, exist_ok=True)
os.makedirs(SHARE, exist_ok=True)


# =====================================================
# SAFE PATH — super aman (anti directory traversal)
# =====================================================
def safe(path):
    if not path:
        return ROOT

    real = os.path.realpath(path)
    root = os.path.realpath(ROOT)

    if not real.startswith(root):
        return root

    return real


# =====================================================
# AUTH CHECK
# =====================================================
def fm_auth():
    if not BMS_auth_is_login():
        return jsonify({"error": "Belum login"}), 403

    if not (BMS_auth_is_admin() or BMS_auth_is_root()):
        return jsonify({"error": "Akses ditolak"}), 403

    return None