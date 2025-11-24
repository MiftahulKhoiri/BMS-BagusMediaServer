import os
from flask import Flask
from flask_cors import CORS

# Import Blueprint Register
from app.routes import register_blueprints


# ======================================================
#   FUNGSI UTAMA: MEMBUAT APLIKASI FLASK
# ======================================================
def create_app():

    # Inisialisasi Flask
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # Secret Key session
    app.config["SECRET_KEY"] = "BAGUS-MEDIA-SERVER-KEY-99999"

    # Izinkan CORS (jika perlu akses dari aplikasi lain)
    CORS(app)

    # Pastikan folder data penting ada
    prepare_bms_folders()

    # Register semua blueprint (dari app/routes/__init__.py)
    register_blueprints(app)

    print(">> BMS Flask App berhasil dibuat!")

    return app


# ======================================================
#   MEMBUAT FOLDER WAJIB UNTUK BMS
# ======================================================
def prepare_bms_folders():
    """
    Membuat folder penting agar BMS berjalan stabil
    di Android (Termux), Linux, atau Windows.
    """

    base_paths = [
        "/storage/emulated/0/BMS",
        "/storage/emulated/0/BMS/MP3",
        "/storage/emulated/0/BMS/VIDEO",
        "/storage/emulated/0/BMS/UPLOAD",
        "/storage/emulated/0/BMS/database",
    ]

    for path in base_paths:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            print(f"[WARN] Tidak bisa membuat folder: {path} -> {e}")


# ======================================================
#   JALANKAN FLASK (KHUSUS RUN STANDALONE)
# ======================================================
if __name__ == "__main__":
    app = create_app()

    # Jalankan server Flask
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )