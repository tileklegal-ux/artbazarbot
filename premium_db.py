import sqlite3
import time
from typing import Optional, Tuple, List

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_premium_table() -> None:
    """
    Таблица premium:
    - user_id — PK
    - until   — UNIX-время окончания (int)
    - tariff  — строка тарифа ('1 месяц', '6 месяцев', '1 год' и т.п.)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium (
            user_id INTEGER PRIMARY KEY,
            until   INTEGER NOT NULL,
            tariff  TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def _get_raw_premium(user_id: int) -> Optional[Tuple[int, str]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT until, tariff FROM premium WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()
    return row if row else None


def has_active_premium(user_id: int) -> bool:
    """
    Проверяем, есть ли активный премиум (until > now).
    """
    row = _get_raw_premium(user_id)
    if not row:
        return False

    until, _ = row
    now_ts = int(time.time())
    return until > now_ts


def get_premium(user_id: int) -> Optional[Tuple[int, str]]:
    """
    Возвращает (until, tariff) или None.
    """
    return _get_raw_premium(user_id)


def set_premium(user_id: int, days: int, tariff: str) -> None:
    """
    Выдача/продление премиума.

    Если у пользователя уже есть активный премиум — добавляем дни к текущему сроку.
    Если премиум истёк или записи нет — считаем от текущего момента.
    """
    now_ts = int(time.time())
    row = _get_raw_premium(user_id)

    if row:
        current_until, _ = row
        if current_until > now_ts:
            # активный — продлеваем от текущего конца
            new_until = current_until + days * 86400
        else:
            # истёк — считаем от текущего момента
            new_until = now_ts + days * 86400
    else:
        new_until = now_ts + days * 86400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO premium (user_id, until, tariff)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            until = excluded.until,
            tariff = excluded.tariff
        """,
        (user_id, new_until, tariff),
    )

    conn.commit()
    conn.close()


def list_premium_users(active_only: bool = True, limit: int = 50) -> List[Tuple[int, int, str]]:
    """
    Возвращает список премиум-пользователей.
    Элементы списка: (user_id, until, tariff).

    active_only = True  -> только те, у кого премиум ещё не истёк.
    active_only = False -> все записи.
    """
    now_ts = int(time.time())
    conn = get_connection()
    cursor = conn.cursor()

    if active_only:
        cursor.execute(
            """
            SELECT user_id, until, tariff
            FROM premium
            WHERE until > ?
            ORDER BY until DESC
            LIMIT ?
            """,
            (now_ts, limit),
        )
    else:
        cursor.execute(
            """
            SELECT user_id, until, tariff
            FROM premium
            ORDER BY until DESC
            LIMIT ?
            """,
            (limit,),
        )

    rows = cursor.fetchall()
    conn.close()
    return rows
