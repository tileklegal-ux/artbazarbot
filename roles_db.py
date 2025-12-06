import sqlite3
from typing import List, Tuple

from config import DB_PATH, OWNER_ID, MANAGER_ID

ROLE_USER = "user"
ROLE_MANAGER = "manager"
ROLE_OWNER = "owner"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_roles_table() -> None:
    """
    Инициализация таблицы ролей.
    Плюс гарантируем, что владелец и дефолтный менеджер записаны в БД.
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
    conn.close()

    # Обновляем (или создаём) записи для владельца и менеджера
    if OWNER_ID:
        set_role(OWNER_ID, ROLE_OWNER)
    if MANAGER_ID:
        set_role(MANAGER_ID, ROLE_MANAGER)


def set_role(user_id: int, role: str) -> None:
    """
    Установить/обновить роль пользователя.
    """
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
    Получить роль пользователя.

    Приоритет:
    1) Если явно записана в таблицу — берём её.
    2) Если user_id совпадает с OWNER_ID — owner.
    3) Если user_id совпадает с MANAGER_ID — manager.
    4) Иначе — обычный user.
    """
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

    if user_id == OWNER_ID:
        return ROLE_OWNER
    if user_id == MANAGER_ID:
        return ROLE_MANAGER

    return ROLE_USER


def is_owner(user_id: int) -> bool:
    """
    Владелец — это тот, у кого роль owner ИЛИ ID совпадает с OWNER_ID.
    """
    return user_id == OWNER_ID or get_role(user_id) == ROLE_OWNER


def is_manager(user_id: int) -> bool:
    """
    Менеджер — роль manager, но владелец тоже имеет доступ как менеджер.
    """
    role = get_role(user_id)
    return role in (ROLE_MANAGER, ROLE_OWNER)


def list_managers() -> List[Tuple[int, str]]:
    """
    Список всех менеджеров и владельцев из таблицы ролей.
    Возвращает список (user_id, role).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, role FROM roles WHERE role IN (?, ?)",
        (ROLE_MANAGER, ROLE_OWNER),
    )
    rows = cursor.fetchall()

    conn.close()
    return rows
