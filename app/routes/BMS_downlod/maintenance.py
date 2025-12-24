import os
import time
from app.BMS_config import BASE_DOWNLOADS_FOLDER
from app.routes.BMS_downlod.db import get_db

def cleanup_file_lama(hari=30):
    batas_waktu = time.time() - (hari * 86400)
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, file_path FROM downloads")
    rows = cur.fetchall()

    dihapus = 0

    for r in rows:
        path = r["file_path"]
        if not path or not os.path.exists(path):
            cur.execute("DELETE FROM downloads WHERE id=?", (r["id"],))
            dihapus += 1
            continue

        if os.path.getmtime(path) < batas_waktu:
            try:
                os.remove(path)
            except Exception:
                pass
            cur.execute("DELETE FROM downloads WHERE id=?", (r["id"],))
            dihapus += 1

    conn.commit()
    conn.close()
    return dihapus