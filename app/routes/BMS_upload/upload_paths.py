import os
from app.BMS_config import BASE

ROOT = os.path.realpath(BASE)
UPLOAD_INTERNAL = ".uploads"
BACKUP_INTERNAL = ".backups"


def safe_path(path):
    if not path:
        return ROOT
    real = os.path.realpath(path)
    if not real.startswith(ROOT):
        return ROOT
    return real


def internal_path(*paths):
    base = os.path.join(ROOT, *paths)
    real = os.path.realpath(base)
    if not real.startswith(ROOT):
        raise Exception("Blocked path traversal attempt")
    return real