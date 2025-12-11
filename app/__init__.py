import os
from flask import Flask, render_template, session
from flask_cors import CORS
from flask_sock import Sock

# Import config
from app.BMS_config import BASE

# Auto repair DB
from app.database.BMS_auto_repair import (
    ensure_users_table,
    ensure_root_user,
    ensure_videos_table,
    ensure_folders_table,
    ensure_mp3_tables
)

# Register Blueprint
from app.routes import register_blueprints

# Register WebSocket (update system)
from app.routes.BMS_update import register_ws


# ======================================================
#   DATABASE INITIALIZER
# ======================================================
def init_database():
    """Memastikan semua tabel penting tersedia."""
    ensure_users_table()
    ensure_root_user()
    ensure_folders_table()
    ensure_videos_table()
    ensure_mp3_tables()


# ======================================================
#   CREATE FLASK APP
# ======================================================
def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # SECRET KEY
    app.config["SECRET_KEY"] = os.environ.get(
        "BMS_SECRET",
        "BAGUS-MEDIA-SERVER-KEY-99999"
    )

    # PROJECT ROOT
    app.config["PROJECT_ROOT"] = (
        "/data/data/com.termux/files/home/BMS-BagusMediaServer"
    )

    # Inisialisasi Database
    init_database()

    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register Blueprints
    register_blueprints(app)

    # Register WebSocket
    try:
        sock = Sock(app)
        register_ws(sock)
        print(">> WebSocket berhasil diregistrasi!")
    except Exception as e:
        print(f"[ERROR] Gagal mendaftarkan WebSocket: {e}")

    print(">> BMS Flask App berhasil dibuat!")
    print(f">> BASE Folder : {BASE}")

    # ==================================================
    #   HOME ROUTE
    # ==================================================
    @app.route("/")
    def BMS_home():

        # Jika belum login → welcome
        if "user_id" not in session:
            return render_template("BMS_welcome.html")

        # ROOT
        if session.get("role") == "root":
            return render_template("BMSadmin_home.html")

        # USER
        return render_template("BMSuser_home.html")

    # ==================================================
    #   ERROR HANDLER
    # ==================================================
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error_403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error_500.html"), 500

    return app


# ======================================================
#   RUN SERVER
# ======================================================
if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=80,
        debug=True
    )