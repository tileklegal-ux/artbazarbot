import sqlite3
import time
from config import DB_PATH


def init_premium_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS premium (
        user_id INTEGER PRIMARY KEY,
        until INTEGER NOT NULL,
        tariff TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def set_premium(user_id: int, days: int, tariff: str):
    """Выдаёт премиум: если премиум активен — продлевает."""
    now = int(time.time())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Проверяем, есть ли активный премиум
    c.execute("SELECT until FROM premium WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if row:
        current_until = row[0]
        # Если премиум активен — продлеваем
        if current_until > now:
            until = current_until + (days * 86400)
        else:
            until = now + (days * 86400)
    else:
        until = now + (days * 86400)

    c.execute("""
        INSERT INTO premium (user_id, until, tariff)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET until=excluded.until, tariff=excluded.tariff
    """, (user_id, until, tariff))

    conn.commit()
    conn.close()

    return until


def has_active_premium(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = int(time.time())

    c.execute("SELECT until FROM premium WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    return bool(row and row[0] > now)


def get_premium(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT until, tariff FROM premium WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    conn.close()
    return row if row else (None, None)
