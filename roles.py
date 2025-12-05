# ---------- Роли и доступы ----------

# Владелец бота (имеет полный доступ)
OWNER_ID = 1974482384  # Тилек

# Менеджеры (можно добавлять динамически позже)
MANAGERS = {571499876}  # Artbazar_support


# Проверка: является ли пользователь владельцем
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# Проверка: является ли пользователь менеджером
def is_manager(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in MANAGERS


# Проверка: обычный пользователь
def is_user(user_id: int) -> bool:
    return True
