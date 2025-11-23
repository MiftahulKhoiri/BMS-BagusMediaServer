import sqlite3
import os

DB_PATH = "bms.db"

def BMS_db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def BMS_db_init():
    """Membuat tabel user jika belum ada."""
    conn = BMS_db_connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def BMS_db_create_root(username, password):
    """Membuat akun root pertama kali."""
    import hashlib

    conn = BMS_db_connect()
    cur = conn.cursor()

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    try:
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed_pw, "root"))
        conn.commit()
    except:
        # Jika sudah ada root, jangan error
        pass

    conn.close()