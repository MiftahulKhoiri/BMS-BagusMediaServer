import sqlite3
import os
from app.BMS_config import DOWNLOADS_FOLDER

DB_PATH = os.path.join(DOWNLOADS_FOLDER, "download_history.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipe TEXT,
            title TEXT,
            file_path TEXT,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def ambil_semua_download(limit=50):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, tipe, title, file_path, source_url, created_at
        FROM downloads
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]