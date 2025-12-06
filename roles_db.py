import sqlite3
from config import DB_PATH, OWNER_ID, MANAGER_ID


def init_roles_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        user_id INTEGER PRIMARY KEY,
        role TEXT NOT NULL
    )
    """)

    # Добавляем владельца, если его нет
    c.execute("SELECT role FROM roles WHERE user_id = ?", (OWNER_ID,))
    if c.fetchone() is None:
        c.execute("INSERT INTO roles (user_id, role) VALUES (?, ?)", (OWNER_ID, "owner"))

    # Добавляем менеджера, если его нет
    c.execute("SELECT role FROM roles WHERE user_id = ?", (MANAGER_ID,))
    if c.fetchone() is None:
        c.execute("INSERT INTO roles (user_id, role) VALUES (?, ?)", (MANAGER_ID, "manager"))

    conn.commit()
    conn.close()


def set_role(user_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO roles (user_id, role)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET role=excluded.role
    """, (user_id, role))
    conn.commit()
    conn.close()


def get_role(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role FROM roles WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "user"
    return row[0]


def is_owner(user_id: int) -> bool:
    return get_role(user_id) == "owner"


def is_manager(user_id: int) -> bool:
    return get_role(user_id) == "manager"
