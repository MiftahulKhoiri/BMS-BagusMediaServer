# =======================================================
#   BMS ROUTES INITIALIZER (FINAL & CLEAN)
#   Modul ini mendaftarkan seluruh Blueprint ke Flask App
#   tanpa duplikasi & aman dari error import.
# =======================================================

# ====================================
#  IMPORT BLUEPRINTS BMS
# ====================================

# Auth baru (modular)
from app.routes.BMS_auth import auth
from app.routes.BMS_file_manager import fm_premium
# Core logger
from .BMS_logger import logger

# User / Admin Panel
from .BMS_user import user
from .BMS_admin import admin

# Video & MP3 (modular)
from .BMS_video import blueprints as video_blueprints
from .BMS_mp3 import blueprints as mp3_blueprints

# System & Tools
from .BMS_update import update
from .BMS_profile import profile
from app.routes.BMS_upload import upload
from .BMS_systeminfo import systeminfo
from .BMS_terminal import terminal
from .BMS_power import BMS_power


# =======================================================
#   FUNGSI REGISTER BLUEPRINTS
# =======================================================
def register_blueprints(app):

    BLUEPRINTS = [
        auth,        
        logger,
        user,
        admin,
        update,
        profile,
        fm_premium,
        upload,
        systeminfo,
        terminal,
        BMS_power,
    ]

    # Tambahkan blueprint modular MP3 & Video
    BLUEPRINTS += video_blueprints
    BLUEPRINTS += mp3_blueprints

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