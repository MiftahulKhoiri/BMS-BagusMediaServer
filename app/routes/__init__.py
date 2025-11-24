# =======================================================
#   BMS ROUTES INITIALIZER
#   Modul ini bertugas mendaftarkan semua Blueprint
#   ke dalam aplikasi Flask utama.
# =======================================================

from .BMS_admin import admin
from .BMS_user import user
from .BMS_auth import auth

from .BMS_media_mp3 import media_mp3
from .BMS_media_video import media_video

from .BMS_upload import upload
from .BMS_update import update

from .BMS_profile import profile
from .BMS_filemanager import filemanager

from .BMS_systeminfo import systeminfo
from .BMS_terminal import terminal
from .BMS_logger import logger


# =======================================================
#   FUNGSI REGISTER BLUEPRINT
# =======================================================
def register_blueprints(app):
    """  
    Fungsi untuk mendaftarkan seluruh route Blueprint  
    ke dalam aplikasi utama Flask.
    """

    # Authentication (Login/Register/Logout)
    app.register_blueprint(auth)

    # User Panel
    app.register_blueprint(user)

    # Admin Panel
    app.register_blueprint(admin)

    # Media
    app.register_blueprint(media_mp3)
    app.register_blueprint(media_video)

    # Upload File
    app.register_blueprint(upload)

    # Update Server
    app.register_blueprint(update)

    # Profile (User Profile)
    app.register_blueprint(profile)

    # File Manager
    app.register_blueprint(filemanager)

    # System Info
    app.register_blueprint(systeminfo)

    # Terminal
    app.register_blueprint(terminal)
    

    app.register_blueprint(logger)

    print(">> Semua Blueprint BMS berhasil terdaftar!")