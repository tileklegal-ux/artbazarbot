import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'ru'
        )
    """)
    conn.commit()
    conn.close()

def get_user_language(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "ru"

def set_user_language(user_id, username, lang):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (user_id, username, language)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language = ?
    """, (user_id, username, lang, lang))
    conn.commit()
    conn.close()
