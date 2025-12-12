import time
from flask import session

DEFAULT_SESSION_MINUTES = 60

def BMS_auth_is_login():
    if not session.get("user_id"):
        return False

    if not session.get("username"):
        return False

    expiry_ts = session.get("_expiry_ts")
    now = int(time.time())

    if not expiry_ts or now > int(expiry_ts):
        session.clear()
        return False

    return True

def BMS_auth_is_admin():
    return BMS_auth_is_login() and session.get("role") == "admin"

def BMS_auth_is_root():
    return BMS_auth_is_login() and session.get("role") == "root"