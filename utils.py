from typing import Dict

from messages_ru import texts as ru_texts
from messages_kg import texts as kg_texts
from messages_kz import texts as kz_texts
from database import get_user_language

LANG_TEXTS: Dict[str, Dict[str, str]] = {
    "ru": ru_texts,
    "kg": kg_texts,
    "kz": kz_texts,
}


def get_text(user_id: int, key: str) -> str:
    """
    Возвращает текст по ключу с учётом языка пользователя.
    Если язык не найден или ключ неизвестен — откатываемся в русский
    и/или возвращаем сам ключ (для отладки).
    """
    lang = get_user_language(user_id) or "ru"
    if lang not in LANG_TEXTS:
        lang = "ru"
    lang_dict = LANG_TEXTS.get(lang, ru_texts)
    return lang_dict.get(key, ru_texts.get(key, key))
