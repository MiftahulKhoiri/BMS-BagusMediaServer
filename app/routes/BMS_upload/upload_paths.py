import os
from app.BMS_config import BASE
from app.BMS_config import VIDEO_FOLDER,


ROOT = os.path.realpath(BASE)

UPLOAD_INTERNAL = os.path.join(ROOT, ".uploads")
BACKUP_INTERNAL = os.path.join(ROOT, ".backups")

os.makedirs(UPLOAD_INTERNAL, exist_ok=True)
os.makedirs(BACKUP_INTERNAL, exist_ok=True)

def internal_path(*paths):
    base = os.path.join(ROOT, *paths)
    real = os.path.realpath(base)
    if not real.startswith(ROOT):
        raise RuntimeError("Blocked path traversal")
    return real