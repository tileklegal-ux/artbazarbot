from premium_db import has_active_premium
from usage_db import get_today_usage, log_usage
from utils import get_text

DAILY_LIMIT = 3  # лимит бесплатного тарифа


def check_limit(user_id: int):
    """
    Возвращает:
      (True, None)  — можно использовать (лимит не превышен или есть премиум)
      (False, text) — лимит превышен, text содержит сообщение для пользователя
    """

    # Премиум — без ограничений
    if has_active_premium(user_id):
        log_usage(user_id)
        return True, None

    used = get_today_usage(user_id)

    if used >= DAILY_LIMIT:
        return False, get_text(user_id, "premium_info_no")

    # Лимит не превышен — считаем запрос
    log_usage(user_id)
    return True, None
