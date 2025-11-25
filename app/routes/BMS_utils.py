# ============================================================
#   BMS – UTILS (Role Security, Login Check, Permission Tools)
# ============================================================

from flask import session, abort

utils = Blueprint("auth", __name__, url_prefix="/utils")


def require_root():
    """
    Mengizinkan akses hanya untuk user dengan role 'root' atau 'admin'.
    Dipanggil di setiap route Blueprint admin.
    """

    role = session.get("role")

    # Jika tidak login → tolak
    if role is None:
        return abort(403)

    # Jika bukan root/admin → tolak
    if role not in ("root", "admin"):
        return abort(403)

    return None


def require_login():
    """
    Cek apakah user sudah login.
    Bisa digunakan untuk halaman user biasa.
    """
    if "user_id" not in session:
        return abort(403)

    return None


def current_user_role():
    """
    Mengambil role saat ini dengan aman.
    Bisa dipakai untuk debugging atau tampilan UI.
    """
    return session.get("role", None)