DEFAULT_LANGUAGE = "ru"

SUPPORTED_LANGUAGES = ["ru", "kg", "kz"]

LANG_FILES = {
    "ru": "messages_ru",
    "kg": "messages_kg",
    "kz": "messages_kz",
}

# OPENAI ключ брать из переменной окружения на Fly
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DB_PATH = "database.db"
