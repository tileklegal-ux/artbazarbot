import sqlite3

DB_PATH = "database.db"


def init_roles_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY,
            role TEXT
        )
    """)

    conn.commit()
    conn.close()


def set_role(user_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO roles (user_id, role)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET role = excluded.role
    """, (user_id, role))

    conn.commit()
    conn.close()


def get_role(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT role FROM roles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else "user"
