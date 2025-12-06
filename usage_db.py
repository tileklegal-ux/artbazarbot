import sqlite3
from datetime import datetime
from typing import List, Tuple

from config import DB_PATH


def init_usage_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        ts INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def log_usage(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    date = _today_str()
    ts = int(datetime.utcnow().timestamp())

    c.execute(
        "INSERT INTO usage_logs (user_id, date, ts) VALUES (?, ?, ?)",
        (user_id, date, ts),
    )

    conn.commit()
    conn.close()


def get_today_usage(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    date = _today_str()
    c.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE user_id = ? AND date = ?",
        (user_id, date),
    )
    row = c.fetchone()
    conn.close()

    return row[0] if row else 0


def get_last_requests(user_id: int, limit: int = 20) -> List[Tuple[int, str, int]]:
    """
    Возвращает последние N записей по пользователю:
    (id, date, ts)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT id, date, ts FROM usage_logs "
        "WHERE user_id = ? ORDER BY ts DESC LIMIT ?",
        (user_id, limit),
    )
    rows = c.fetchall()
    conn.close()

    return rows
