import os
from flask import Flask, redirect, render_template, session
from flask_cors import CORS

# Import config
from app.BMS_config import BASE

# Auto repair DB
from app.database.BMS_auto_repair import ensure_users_table, ensure_root_user

# Import Blueprint register
from app.routes import register_blueprints


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

    # ===========================================
    # 🔥 Jalankan Auto Repair DB sebelum blueprint
    # ===========================================
    app.config["PROJECT_ROOT"] ="/data/data/com.termux/files/home/BMS-BagusMediaServer"
    ensure_users_table()
    ensure_root_user()

    # ===========================================
    # 🔥 CORS
    # ===========================================
    CORS(app, resources={r"/*": {"origins": [
        "http://localhost",
        "http://127.0.0.1",
        "http://0.0.0.0",
        "http://localhost:5000"
    ]}})

    # ===========================================
    # 🔥 Register semua blueprint
    # ===========================================
    register_blueprints(app)

    print(">> BMS Flask App berhasil dibuat!")
    print(f">> BASE Folder: {BASE}")

    # ===========================================
    # HOME ROUTE
    # ===========================================
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
#   RUN SERVER
# ======================================================
if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )