import time
import shutil
from .upload_sessions import upload_sessions, upload_lock

SESSION_TIMEOUT = 3600  # 1 jam

def cleanup_sessions():
    now = time.time()

    with upload_lock:
        dead = [
            sid for sid, info in upload_sessions.items()
            if now - info["created"] > SESSION_TIMEOUT
        ]

        for sid in dead:
            shutil.rmtree(upload_sessions[sid]["tmp_dir"], ignore_errors=True)
            del upload_sessions[sid]