# =======================================================
#   BMS ROUTES INITIALIZER
#   Modul ini mendaftarkan seluruh Blueprint ke Flask App
#   dengan keamanan & debugging yang lebih baik.
# =======================================================

from flask import Blueprint

# Core
from .BMS_auth import auth
from .BMS_logger import logger

# User / Admin Panel
from .BMS_user import user
from .BMS_admin import admin

# Media Modules
from .BMS_media_mp3 import media_mp3
from .BMS_media_video import media_video

# System & Tools
from .BMS_update import update
from .BMS_profile import profile
from .BMS_filemanager_premium import fm_premium
from .BMS_upload import upload
from .BMS_systeminfo import systeminfo
from .BMS_terminal import terminal
from .BMS_power import BMS_power   # gunakan relative import agar konsisten


# =======================================================
#   REGISTER BLUEPRINTS SAFELY
# =======================================================
def register_blueprints(app):

    BLUEPRINTS = [
        auth,
        logger,
        user,
        admin,
        media_mp3,
        media_video,
        update,
        profile,
        fm_premium,
        upload,
        systeminfo,
        terminal,
        BMS_power
    ]

    print("\n>> ===============================")
    print(">>   REGISTERING BMS BLUEPRINTS")
    print(">> ===============================")

    for bp in BLUEPRINTS:
        try:
            app.register_blueprint(bp)
            print(f"✔ Blueprint registered: /{bp.url_prefix or ''}  ({bp.name})")

        except Exception as e:
            print(f"✖ ERROR loading blueprint '{bp.name}': {e}")

    print(">> Semua Blueprint BMS berhasil terdaftar!\n")

    return app