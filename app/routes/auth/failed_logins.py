import time
from flask import current_app
from .db import get_db

DEFAULT_LOCK_THRESHOLD = 5
DEFAULT_LOCK_WINDOW_MIN = 15

def add_failed_attempt(username, ip):
    conn = get_db()
    conn.execute(
        "INSERT INTO failed_logins (username, ip, ts) VALUES (?, ?, ?)",
        (username, ip, int(time.time()))
    )
    conn.commit()
    conn.close()

def count_failed_attempts(username, ip, minutes_window):
    cutoff = int(time.time()) - (minutes_window * 60)
    conn = get_db()
    cur = conn.execute("""
        SELECT COUNT(*) as c
        FROM failed_logins
        WHERE (username = ? OR ip = ?) AND ts >= ?
    """, (username, ip, cutoff))
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0

def clear_failed_attempts(username, ip):
    conn = get_db()
    conn.execute("DELETE FROM failed_logins WHERE username = ? OR ip = ?", (username, ip))
    conn.commit()
    conn.close()

def is_locked(username, ip):
    threshold = current_app.config.get("BMS_LOCK_THRESHOLD", DEFAULT_LOCK_THRESHOLD)
    window = current_app.config.get("BMS_LOCK_WINDOW_MIN", DEFAULT_LOCK_WINDOW_MIN)
    attempts = count_failed_attempts(username, ip, window)
    return attempts >= threshold