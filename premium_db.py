import sqlite3
import time
from typing import Optional, Tuple

from config import DB_PATH


def _conn():
    return sqlite3.connect(DB_PATH)


def init_premium_table():
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS premium (
            user_id     INTEGER PRIMARY KEY,
            until_ts    INTEGER NOT NULL,
            tariff      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def set_premium(user_id: int, days: int, tariff: str) -> None:
    until_ts = int(time.time()) + days * 24 * 60 * 60

    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO premium(user_id, until_ts, tariff)
        VALUES(?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            until_ts = excluded.until_ts,
            tariff   = excluded.tariff
        """,
        (user_id, until_ts, tariff),
    )
    conn.commit()
    conn.close()


def get_premium(user_id: int) -> Optional[Tuple[int, str]]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT until_ts, tariff FROM premium WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return int(row[0]), row[1]


def has_active_premium(user_id: int) -> bool:
    data = get_premium(user_id)
    if not data:
        return False
    until_ts, _ = data
    return until_ts > int(time.time())
