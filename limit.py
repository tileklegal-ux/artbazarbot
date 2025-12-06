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

    # Премиум — без ограничений, но всё равно логируем
    if has_active_premium(user_id):
        log_usage(user_id)
        return True, None

    used_today = get_today_usage(user_id)

    if used_today >= DAILY_LIMIT:
        # Текст из messages_xx по языку пользователя
        template = get_text(user_id, "limit_exceeded")
        try:
            msg = template.format(limit=DAILY_LIMIT, used=used_today)
        except Exception:
            # если вдруг нет плейсхолдеров — просто отправляем строку как есть
            msg = template
        return False, msg

    # Лимит не превышен — логируем запрос
    log_usage(user_id)
    return True, None
