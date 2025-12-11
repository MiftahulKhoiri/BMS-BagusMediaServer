# ============================================================================
#   USER IDENTIFIER — Sistem video per-user
# ============================================================================
def current_user_identifier():
    """
    Mengembalikan ID unik user, sama seperti modul MP3.
    Terjamin tidak None dan konsisten.
    """
    if session.get("user_id") is not None:
        return str(session.get("user_id"))

    if session.get("username") is not None:
        return str(session.get("username"))

    # fallback aman jika tidak login
    return "anonymous"