# ============================================================================
#   MP4 MODULE BLUEPRINT EXPORTER
# ============================================================================

from .BMS_video_routes import video_routes
from .BMS_video_scan import video_scan

blueprints = [
    video_routes,
    video_scan
]