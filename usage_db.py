import sqlite3
import time
from datetime import datetime

DB_PATH = "database.db"


def init_usage_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def log_usage(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usage_logs (user_id, timestamp) VALUES (?, ?)",
        (user_id, int(time.time())),
    )

    conn.commit()
    conn.close()


def get_today_usage(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    start_of_day = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp()

    cursor.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE user_id = ? AND timestamp >= ?",
        (user_id, start_of_day),
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count
