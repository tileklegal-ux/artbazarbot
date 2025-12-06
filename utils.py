from database import get_user_language
from messages_ru import TEXTS as RU
from messages_kg import TEXTS as KG
from messages_kz import TEXTS as KZ


LANG_MAP = {
    "ru": RU,
    "kg": KG,
    "kz": KZ,
}


def get_text(user_id: int, key: str) -> str:
    """
    Возвращает строку из языкового словаря.
    Если ключ не найден — возвращает сам key (чтобы не падать).
    """
    lang = get_user_language(user_id) or "ru"
    texts = LANG_MAP.get(lang, RU)
    return texts.get(key, key)
