import sqlite3
import time

DB_PATH = "database.db"


def init_premium_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_access (
            user_id INTEGER PRIMARY KEY,
            until INTEGER NOT NULL,
            tariff TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def set_premium(user_id: int, days: int, tariff: str):
    until = int(time.time()) + days * 24 * 3600

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO premium_access (user_id, until, tariff)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET until=excluded.until, tariff=excluded.tariff
        """,
        (user_id, until, tariff),
    )

    conn.commit()
    conn.close()


def has_active_premium(user_id: int) -> bool:
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT until FROM premium_access WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    return row[0] > now


def get_premium(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT until, tariff FROM premium_access WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()
    return row
