import sqlite3
from app.BMS_config import DB_PATH

def log_upload(filename, size, user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS upload_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            size INTEGER,
            user TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute(
        "INSERT INTO upload_logs (filename, size, user) VALUES (?, ?, ?)",
        (filename, size, user)
    )

    conn.commit()
    conn.close()