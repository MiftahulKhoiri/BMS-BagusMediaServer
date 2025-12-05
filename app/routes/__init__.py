# =======================================================
#   BMS ROUTES INITIALIZER
#   Modul ini mengatur semua Blueprint ke dalam Flask App
# =======================================================

from .BMS_auth import auth
from .BMS_logger import logger

from .BMS_user import user
from .BMS_admin import admin

from .BMS_media_mp3 import media_mp3
from .BMS_media_video import media_video

from .BMS_update import update
from .BMS_profile import profile
from .BMS_filemanager_premium import fm_premium
from .BMS_upload import upload
from .BMS_systeminfo import systeminfo
from .BMS_terminal import terminal
from app.routes.BMS_power import BMS_power


# =======================================================
#   REGISTER SEMUA BLUEPRINT
# =======================================================
def register_blueprints(app):

    # --- Core Auth ---
    app.register_blueprint(auth)
    app.register_blueprint(logger)

    # --- User & Admin Panel ---
    app.register_blueprint(user)
    app.register_blueprint(admin)

    # --- Media ---
    app.register_blueprint(media_mp3)
    app.register_blueprint(media_video)

    # --- Tools / System ---
    app.register_blueprint(update)
    app.register_blueprint(profile)

    # FileManager Premium
    app.register_blueprint(fm_premium)
    app.register_blueprint(upload)

    app.register_blueprint(systeminfo)
    app.register_blueprint(terminal)
    app.register_blueprint(BMS_power)

    print(">> Semua Blueprint BMS berhasil terdaftar!")

    return app