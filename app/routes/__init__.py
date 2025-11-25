# =======================================================
#   BMS ROUTES INITIALIZER
#   Modul ini mengatur semua Blueprint ke dalam Flask App
# =======================================================

from .BMS_auth import auth
from .BMS_logger import logger
from .BMS_utils import utils

from .BMS_user import user
from .BMS_admin import admin

from .BMS_media_mp3 import media_mp3
from .BMS_media_video import media_video

from .BMS_upload import upload
from .BMS_update import update
from .BMS_profile import profile
from .BMS_filemanager import filemanager
from .BMS_systeminfo import systeminfo
from .BMS_terminal import terminal


# =======================================================
#   REGISTER SEMUA BLUEPRINT
# =======================================================
def register_blueprints(app):
    """
    Mendaftarkan seluruh blueprint BMS ke aplikasi Flask.
    Urutan dibuat logis: Auth → Logger → User → Admin → Modules
    """

    # --- Core Auth ---
    app.register_blueprint(auth)
    app.register_blueprint(logger)
    app.register_blueprint(utils)

    # --- User & Admin Panel ---
    app.register_blueprint(user)
    app.register_blueprint(admin)

    # --- Media ---
    app.register_blueprint(media_mp3)
    app.register_blueprint(media_video)

    # --- Tools / System ---
    app.register_blueprint(upload)
    app.register_blueprint(update)
    app.register_blueprint(profile)
    app.register_blueprint(filemanager)
    app.register_blueprint(systeminfo)
    app.register_blueprint(terminal)

    print(">> Semua Blueprint BMS berhasil terdaftar!")

    return app