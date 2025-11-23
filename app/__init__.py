from flask import Flask

def create_app():
    app = Flask(__name__)

    # Registrasi blueprint khusus BMS
    from .routes.BMS_main import main
    app.register_blueprint(main)

    return app