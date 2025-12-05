import sqlite3
from typing import Optional

from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Базовая таблица пользователей (язык и т.п.).
    Остальные таблицы (роли, премиум) живут в своих файлах, но используют тот же DB_PATH.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            language    TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def set_user_language(user_id: int, language: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users(user_id, language)
        VALUES(?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """,
        (user_id, language),
    )
    conn.commit()
    conn.close()


def get_user_language(user_id: int) -> Optional[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
