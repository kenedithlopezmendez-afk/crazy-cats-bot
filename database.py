import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "little_boxes.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boxes (
                thread_id INTEGER PRIMARY KEY,
                owner_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                fecha_adquisicion TEXT NOT NULL,
                fecha_expiracion TEXT NOT NULL,
                mensaje_fijado_id INTEGER
            )
        """)
        conn.commit()