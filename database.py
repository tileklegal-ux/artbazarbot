import sqlite3
from typing import Optional

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """
    Базовая таблица пользователей:
    - user_id      — Telegram ID
    - username     — @username (если есть)
    - first_name   — имя
    - last_name    — фамилия
    - language     — 'ru' / 'kg' / 'kz'
    - created_at   — ISO-строка
    - updated_at   — ISO-строка
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY,
            username   TEXT,
            first_name TEXT,
            last_name  TEXT,
            language   TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def upsert_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> None:
    """
    Заводим пользователя, если его ещё нет.
    Если уже есть — просто обновляем username / имя / фамилию.
    Язык тут не трогаем, он отдельной функцией.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Проверяем, есть ли запись
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE users
            SET username = COALESCE(?, username),
                first_name = COALESCE(?, first_name),
                last_name = COALESCE(?, last_name),
                updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (username, first_name, last_name, user_id),
        )
    else:
        cur.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, language, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (user_id, username, first_name, last_name, "ru"),
        )

    conn.commit()
    conn.close()


def set_user_language(user_id: int, language: str) -> None:
    """
    Устанавливаем язык пользователя.
    Если пользователя ещё нет — создаём его с базовыми данными и этим языком.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE users
            SET language = ?,
                updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (language, user_id),
        )
    else:
        # минимальная запись, если юзера ещё нет
        cur.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, language, created_at, updated_at)
            VALUES (?, NULL, NULL, NULL, ?, datetime('now'), datetime('now'))
            """,
            (user_id, language),
        )

    conn.commit()
    conn.close()


def get_user_language(user_id: int) -> Optional[str]:
    """
    Возвращает язык пользователя ('ru' / 'kg' / 'kz') или None, если не найден.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None
