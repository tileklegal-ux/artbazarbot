import os

# Токен бота из Fly.io secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")

# URL приложения на Fly.io
# ОБЯЗАТЕЛЬНО: приведи к реальному имени приложения из fly.toml
# В твоём случае в fly.toml: app = "artbazarbot" → значит:
APP_URL = "https://artbazarbot.fly.dev"

# Вебхук
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"

# Путь к базе данных (один файл для всех модулей)
DB_PATH = "database.db"

# Роли по умолчанию (под твой ТЗ)
OWNER_ID = 1974482384
MANAGER_ID = 571499876

OWNER_USERNAME = "@ihaariss"
MANAGER_USERNAME = "@Artbazar_support"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# модель можно переопределить через переменную окружения, если захочешь
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
