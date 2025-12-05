from messages_ru import texts as ru_texts
from messages_kg import texts as kg_texts
from messages_kz import texts as kz_texts

LANG_TEXTS = {
    "ru": ru_texts,
    "kg": kg_texts,
    "kz": kz_texts,
}


def get_text(lang: str, key: str) -> str:
    lang_dict = LANG_TEXTS.get(lang, ru_texts)
    return lang_dict.get(key, ru_texts.get(key, key))
