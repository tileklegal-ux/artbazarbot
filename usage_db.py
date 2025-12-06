import sqlite3
import time
from datetime import datetime

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_usage_table() -> None:
    """
    Таблица usage_logs:
    - id        — PK
    - user_id   — Telegram ID
    - action    — тип действия (analyze / niche / reco / margin / etc.)
    - timestamp — UNIX-время (int)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def log_usage(user_id: int, action: str = "request") -> None:
    """
    Логируем один запрос пользователя.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_ts = int(time.time())

    cursor.execute(
        "INSERT INTO usage_logs (user_id, action, timestamp) VALUES (?, ?, ?)",
        (user_id, action, now_ts),
    )

    conn.commit()
    conn.close()


def get_today_usage(user_id: int) -> int:
    """
    Количество запросов за текущие сутки (по локальному времени сервера).
    """
    conn = get_connection()
    cursor = conn.cursor()

    start_of_day = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp()

    cursor.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE user_id = ? AND timestamp >= ?",
        (user_id, int(start_of_day)),
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_recent_usage(user_id: int, limit: int = 10):
    """
    Последние N запросов пользователя (для личного кабинета).
    Возвращаем список кортежей (action, timestamp).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT action, timestamp
        FROM usage_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()

    conn.close()
    return rows
