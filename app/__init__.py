import os
from flask import Flask, redirect, render_template, session
from flask_cors import CORS

# Import config BMS
from app.BMS_config import BASE

# Import Blueprint register
from app.routes import register_blueprints


# ======================================================
#   FUNGSI UTAMA
# ======================================================
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

    # CORS internal only
    CORS(app, resources={r"/*": {"origins": [
        "http://localhost",
        "http://127.0.0.1",
        "http://0.0.0.0",
        "http://localhost:5000"
    ]}})

    # Register semua blueprint
    register_blueprints(app)

    print(">> BMS Flask App berhasil dibuat!")
    print(f">> BASE Folder: {BASE}")

    # ======================================================
    #   ROUTE HOME (Welcome)
    # ======================================================
    @app.route("/")
    def BMS_home():

        # Jika belum login → welcome page
        if "user_id" not in session:
            return render_template("BMS_welcome.html")

        role = session.get("role", "user")

        # ADMIN / ROOT
        if role in ("root", "admin"):
            return redirect("/admin/home")

        # USER
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