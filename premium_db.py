import sqlite3
import time

DB_PATH = "database.db"


# ---------- Инициализация таблицы премиум-подписок ----------
def init_premium_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium (
            user_id INTEGER PRIMARY KEY,
            expires_at INTEGER  -- timestamp UNIX
        )
    """)

    conn.commit()
    conn.close()


# ---------- Выдача премиума ----------
def give_premium(user_id: int, days: int):
    expires_at = int(time.time()) + days * 24 * 3600  # сколько дней длится премиум

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO premium (user_id, expires_at)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at
    """, (user_id, expires_at))

    conn.commit()
    conn.close()


# ---------- Удаление премиума ----------
def remove_premium(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM premium WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()


# ---------- Проверка — есть ли премиум ----------
def has_premium(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT expires_at FROM premium WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    expires_at = row[0]
    return expires_at > int(time.time())


# ---------- Сколько осталось дней ----------
def premium_days_left(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT expires_at FROM premium WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        return 0

    left_seconds = row[0] - int(time.time())
    if left_seconds < 0:
        return 0

    return left_seconds // 86400  # дни
