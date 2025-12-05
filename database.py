import sqlite3

DB_PATH = "database.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT
        )
    """)

    conn.commit()
    conn.close()


def set_user_language(user_id: int, language: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (user_id, language)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language=excluded.language
    """, (user_id, language))

    conn.commit()
    conn.close()


def get_user_language(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    conn.close()
    return row[0] if row else None
