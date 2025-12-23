# ============================================================================
#   BMS MP3 MODULE — BLUEPRINT INITIALIZER
#   Menggabungkan:
#       ✔ scan blueprint
#       ✔ main mp3 routes
# ============================================================================

from .BMS_mp3_routes import media_mp3
from .BMS_mp3_scan import mp3_scan
app.register_blueprint(mp3_thumb)

# daftar blueprint untuk di-import oleh register_blueprints()
blueprints = [
    media_mp3,
    mp3_scan
]