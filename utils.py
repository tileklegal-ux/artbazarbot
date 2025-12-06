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


def get_user_lang(user_id: int) -> str:
    """
    Возвращает язык пользователя по user_id.
    Если в БД нет или язык не поддерживается — 'ru'.
    """
    lang = get_user_language(user_id) or "ru"
    if lang not in LANG_TEXTS:
        lang = "ru"
    return lang


def get_text(user_id: int, key: str) -> str:
    """
    Централизованный доступ к текстам.
    Используем user_id → язык → словарь → строка.
    Если ключ не найден, возвращаем сам ключ для дебага.
    """
    lang = get_user_lang(user_id)
    lang_dict = LANG_TEXTS.get(lang, ru_texts)
    return lang_dict.get(key, ru_texts.get(key, key))
