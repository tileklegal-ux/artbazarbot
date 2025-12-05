import sqlite3
from config import DB_PATH, DEFAULT_LANGUAGE

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Таблица пользователей
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',
            premium_until INTEGER DEFAULT 0,
            created_at INTEGER,
            last_active INTEGER,
            request_count INTEGER DEFAULT 0,
            language TEXT DEFAULT 'ru'
        )
        """
    )

    # Таблица премиум-покупок
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            manager_id INTEGER,
            months INTEGER,
            created_at INTEGER
        )
        """
    )

    conn.commit()
    conn.close()


def create_or_update_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO users (user_id, username, first_name, created_at, last_active)
        VALUES (?, ?, ?, strftime('%s','now'), strftime('%s','now'))
        ON CONFLICT(user_id) DO UPDATE SET last_active = strftime('%s','now')
        """,
        (user_id, username, first_name),
    )

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT user_id, username, first_name, role, premium_until, language FROM users WHERE user_id = ?",
        (user_id,),
    )

    row = c.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "role": row[3],
            "premium_until": row[4],
            "language": row[5],
        }
    return None


def set_language(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()
