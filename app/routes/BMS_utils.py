# ============================================================
#   BMS – UTILS (Security, Role Checks, Smart Error Handling)
# ============================================================

from flask import session, abort, jsonify, request, redirect


# ============================================================
#  HELPER: Detect apakah request ini AJAX/JSON
# ============================================================
def is_json_request():
    return (
        request.is_json or 
        request.headers.get("X-Requested-With") == "XMLHttpRequest" or
        request.headers.get("Accept") == "application/json"
    )


# ============================================================
#  REQUIRE LOGIN (dengan auto redirect atau JSON)
# ============================================================
def require_login():
    if "user_id" not in session:

        # Jika JSON request → kembalikan JSON
        if is_json_request():
            return jsonify({"error": "Belum login"}), 403

        # Kalau bukan JSON → redirect ke login page
        return redirect("/auth/login")

    return None


# ============================================================
#  REQUIRE ADMIN (admin atau root)
# ============================================================
def require_admin():
    role = session.get("role")

    if role not in ("admin", "root"):
        if is_json_request():
            return jsonify({"error": "Akses admin ditolak"}), 403
        return abort(403)

    return None


# ============================================================
#  REQUIRE ROOT SAJA
# ============================================================
def require_root():
    role = session.get("role")

    if role != "root":
        if is_json_request():
            return jsonify({"error": "Akses root ditolak"}), 403
        return abort(403)

    return None


# ============================================================
#  REQUIRE ROLE SPESIFIK (list)
# ============================================================
def require_role(*roles):
    """
    Gunakan: require_role("admin", "root")
    """
    role = session.get("role")

    if role not in roles:
        if is_json_request():
            return jsonify({"error": f"Akses ditolak untuk role '{role}'"}), 403
        return abort(403)

    return None


# ============================================================
#  HELPER: GET CURRENT ROLE & STATUS LOGIN
# ============================================================
def current_role():
    return session.get("role", None)


def is_logged_in():
    return "user_id" in session