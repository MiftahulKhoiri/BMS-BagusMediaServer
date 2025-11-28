import os
from flask import Flask, redirect, render_template, session
from flask_cors import CORS
from flask_sock import Sock    # <-- WAJIB ADA

# Import config
from app.BMS_config import BASE

# Auto repair DB
from app.database.BMS_auto_repair import ensure_users_table, ensure_root_user, ensure_videos_table, ensure_folders_table

# Import Blueprint register
from app.routes import register_blueprints

# Import WebSocket updater
from app.routes.BMS_update import register_ws   # <-- WAJIB ADA


def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config["SECRET_KEY"] = os.environ.get(
        "BMS_SECRET",
        "BAGUS-MEDIA-SERVER-KEY-99999"
    )

    # ==================================================================
    # PROJECT ROOT
    # ==================================================================
    app.config["PROJECT_ROOT"] = "/data/data/com.termux/files/home/BMS-BagusMediaServer"

    # ==================================================================
    # AUTO REPAIR DB
    # ==================================================================
    ensure_users_table()
    ensure_root_user()
    ensure_folders_table()
    ensure_videos_table()

    # ==================================================================
    # CORS
    # ==================================================================
    CORS(app, resources={r"/*": {"origins": "*"}})

    # ==================================================================
    # REGISTER BLUEPRINT
    # ==================================================================
    register_blueprints(app)

    # ==================================================================
    # REGISTER WEBSOCKET (Hal terpenting agar tombol UPDATE jalan)
    # ==================================================================
    sock = Sock(app)
    register_ws(sock)

    print(">> BMS Flask App berhasil dibuat!")
    print(f">> BASE Folder: {BASE}")

    # ==================================================================
    # HOME
    # ==================================================================
    @app.route("/")
    def BMS_home():

        if "user_id" not in session:
            return render_template("BMS_welcome.html")

        role = session.get("role", "user")

        if role in ("root", "admin"):
            return redirect("/admin/home")

        return redirect("/user/home")

    return app


# ======================================================
# RUN SERVER
# ======================================================
if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )