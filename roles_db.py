import sqlite3
from typing import List, Tuple

from config import DB_PATH, OWNER_ID, MANAGER_ID

ROLE_OWNER = "owner"
ROLE_MANAGER = "manager"
ROLE_USER = "user"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_roles_table() -> None:
    """
    Таблица roles:
    - user_id  — PK
    - role     — 'owner' / 'manager' / 'user'
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY,
            role    TEXT NOT NULL
        )
        """
    )

    conn.commit()

    # гарантируем, что владелец и базовый менеджер заданы
    _ensure_default_roles(conn)

    conn.close()


def _ensure_default_roles(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    # владелец
    cursor.execute(
        """
        INSERT INTO roles (user_id, role)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET role = excluded.role
        """,
        (OWNER_ID, ROLE_OWNER),
    )
    # базовый менеджер
    cursor.execute(
        """
        INSERT INTO roles (user_id, role)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO NOTHING
        """,
        (MANAGER_ID, ROLE_MANAGER),
    )
    conn.commit()


def set_role(user_id: int, role: str) -> None:
    if role not in (ROLE_OWNER, ROLE_MANAGER, ROLE_USER):
        role = ROLE_USER

    conn = get_connection()
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
    """
    Возвращает роль пользователя.
    Для OWNER_ID по умолчанию всегда 'owner'.
    Для остальных — чтение из таблицы, если нет — 'user'.
    """
    if user_id == OWNER_ID:
        return ROLE_OWNER

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role FROM roles WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()

    conn.close()

    if row and row[0]:
        return row[0]

    return ROLE_USER


def is_owner(user_id: int) -> bool:
    return get_role(user_id) == ROLE_OWNER


def is_manager(user_id: int) -> bool:
    """
    Менеджером считаем как менеджера, так и владельца.
    """
    role = get_role(user_id)
    return role in (ROLE_MANAGER, ROLE_OWNER)


def list_managers() -> List[Tuple[int, str]]:
    """
    Возвращает список (user_id, role) для менеджеров и владельца.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, role
        FROM roles
        WHERE role IN (?, ?)
        ORDER BY role DESC
        """,
        (ROLE_OWNER, ROLE_MANAGER),
    )
    rows = cursor.fetchall()

    conn.close()
    return rows
