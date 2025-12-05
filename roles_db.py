import sqlite3
from typing import Optional

from config import DB_PATH, OWNER_ID


ROLE_OWNER = "owner"
ROLE_MANAGER = "manager"
ROLE_USER = "user"


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_roles_table():
    """
    Таблица ролей. На старте гарантируем, что OWNER_ID имеет роль owner.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            user_id     INTEGER PRIMARY KEY,
            role        TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Гарантируем, что в БД есть владелец
    if OWNER_ID:
        cur.execute(
            """
            INSERT OR IGNORE INTO roles(user_id, role)
            VALUES(?, ?)
            """,
            (OWNER_ID, ROLE_OWNER),
        )

    conn.commit()
    conn.close()


def set_role(user_id: int, role: str) -> None:
    if role not in (ROLE_OWNER, ROLE_MANAGER, ROLE_USER):
        raise ValueError("Unknown role")

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO roles(user_id, role)
        VALUES(?, ?)
        ON CONFLICT(user_id) DO UPDATE SET role = excluded.role
        """,
        (user_id, role),
    )
    conn.commit()
    conn.close()


def get_role(user_id: int) -> str:
    """
    Всегда возвращает роль. Если нет в БД — создаёт запись как обычного user.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role FROM roles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row:
        role = row[0]
    else:
        role = ROLE_USER
        cur.execute(
            "INSERT INTO roles(user_id, role) VALUES(?, ?)",
            (user_id, role),
        )
        conn.commit()

    conn.close()
    return role


def is_owner(user_id: int) -> bool:
    return get_role(user_id) == ROLE_OWNER


def is_manager(user_id: int) -> bool:
    role = get_role(user_id)
    return role in (ROLE_MANAGER, ROLE_OWNER)


def list_managers() -> list[tuple[int, str]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, role FROM roles
        WHERE role IN (?, ?)
        ORDER BY created_at DESC
        """,
        (ROLE_MANAGER, ROLE_OWNER),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
