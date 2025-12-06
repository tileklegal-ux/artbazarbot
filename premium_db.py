import sqlite3
import time

DB_PATH = "database.db"


def init_premium_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium (
            user_id INTEGER PRIMARY KEY,
            until INTEGER NOT NULL,
            tariff TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def set_premium(user_id: int, days: int, tariff: str):
    """
    Выдаём/обновляем премиум на N дней.
    """
    until_ts = int(time.time()) + days * 24 * 3600

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO premium (user_id, until, tariff)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET until = excluded.until, tariff = excluded.tariff
        """,
        (user_id, until_ts, tariff),
    )

    conn.commit()
    conn.close()


def has_active_premium(user_id: int) -> bool:
    now_ts = int(time.time())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT until FROM premium WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    return row[0] > now_ts


def get_premium(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT until, tariff FROM premium WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()
    return row  # либо (until, tariff), либо None
