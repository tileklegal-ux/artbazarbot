# database.py

import sqlite3
from config import DB_PATH
import time


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',
            premium_until INTEGER DEFAULT 0,
            created_at INTEGER,
            last_active INTEGER,
            request_count INTEGER DEFAULT 0
        )
    """)

    # Premium table
    c.execute("""
        CREATE TABLE IF NOT EXISTS premium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            manager_id INTEGER,
            months INTEGER,
            created_at INTEGER
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT user_id, username, first_name, role, premium_until FROM users WHERE user_id = ?",
              (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "role": row[3],
        "premium_until": row[4],
    }


def save_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())

    c.execute("""
        INSERT OR REPLACE INTO users (user_id, username, first_name, created_at, last_active)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, first_name, now, now))

    conn.commit()
    conn.close()


def update_last_active(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = int(time.time())

    c.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now, user_id))

    conn.commit()
    conn.close()


def activate_premium(user_id, manager_id, months):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())
    premium_seconds = months * 30 * 24 * 60 * 60

    c.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if row and row[0] > now:
        new_until = row[0] + premium_seconds
    else:
        new_until = now + premium_seconds

    c.execute("UPDATE users SET premium_until = ? WHERE user_id = ?", (new_until, user_id))

    c.execute("""
        INSERT INTO premium (user_id, manager_id, months, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, manager_id, months, now))

    conn.commit()
    conn.close()


def user_has_premium(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())
    c.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    return row[0] > now
