import sqlite3

DB_PATH = "database.db"


def init_roles_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def set_role(user_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO roles (user_id, role)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET role = excluded.role
        """,
        (user_id, role),
    )

    conn.commit()
    conn.close()


def get_role(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role FROM roles WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()

    if row and row[0]:
        return row[0]

    # по умолчанию — обычный пользователь
    return "user"
