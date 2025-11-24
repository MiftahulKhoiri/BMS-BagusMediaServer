import os
from flask import Flask, redirect, render_template, session
from flask_cors import CORS

# Register blueprint dari app/routes
from app.routes import register_blueprints


# ======================================================
#   FUNGSI UTAMA: MEMBUAT APLIKASI FLASK
# ======================================================
def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # --- Secret Key (aman & fleksibel) ---
    app.config["SECRET_KEY"] = os.environ.get(
        "BMS_SECRET",
        "BAGUS-MEDIA-SERVER-KEY-99999"
    )

    # --- CORS aman: hanya izinkan internal access ---
    CORS(app, resources={r"/*": {"origins": [
        "http://localhost",
        "http://127.0.0.1",
        "http://0.0.0.0",
        "http://localhost:5000"
    ]}})

    # Siapkan folder penting
    prepare_bms_folders()

    # Daftarkan semuanya (auth, user, admin, explorer, media, logger, dll)
    register_blueprints(app)

    print(">> BMS Flask App berhasil dibuat!")

    # ======================================================
    #   ✓ ROUTE HOME (WELCOME PAGE)
    # ======================================================
    @app.route("/")
    def BMS_home():
        """
        Halaman utama BMS.
        Jika user belum login → tampilkan Welcome Page.
        Jika sudah login → arahkan sesuai role.
        """
        if "user_id" not in session:
            return render_template("BMS_welcome.html")

        # user sudah login → arahkan ke panel berdasarkan role
        role = session.get("role")

        if role in ("root", "admin"):
            return redirect("/admin/dashboard")

        return redirect("/user/home")

    return app



# ======================================================
#   MEMBUAT FOLDER WAJIB UNTUK BMS
# ======================================================
def prepare_bms_folders():
    """
    Membuat folder penting agar BMS berjalan stabil
    di Android (Termux), Linux, dan Windows.
    """

    # Deteksi OS (Android / PC)
    if os.path.exists("/storage/emulated/0/"):
        BASE = "/storage/emulated/0/BMS"
    else:
        BASE = os.path.expanduser("~/BMS")

    base_paths = [
        BASE,
        f"{BASE}/MP3",
        f"{BASE}/VIDEO",
        f"{BASE}/UPLOAD",
        f"{BASE}/database",
        f"{BASE}/logs"
    ]

    for path in base_paths:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            print(f"[WARN] Tidak bisa membuat folder: {path} -> {e}")


# ======================================================
#   JALANKAN SERVER (standalone mode)
# ======================================================
if __name__ == "__main__":
    app = create_app()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )