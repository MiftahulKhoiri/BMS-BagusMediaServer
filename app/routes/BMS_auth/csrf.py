import secrets
from flask import session

def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return session["csrf_token"]

def verify_csrf(token_from_form):
    token = session.get("csrf_token")
    if not token or not token_from_form:
        return False

    try:
        from secrets import compare_digest
        return compare_digest(token, token_from_form)
    except Exception:
        return token == token_from_form