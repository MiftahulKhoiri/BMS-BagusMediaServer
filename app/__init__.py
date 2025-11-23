from flask import Flask
from app.routes import main, auth, admin, tools, filem, mp3, video, user


def create_app():
    app = Flask(__name__)

    # Registrasi blueprint khusus BMS
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(tools)
    app.register_blueprint(filem)
    app.register_blueprint(mp3)
    app.register_blueprint(video)
    app.register_blueprint(user)

    return app