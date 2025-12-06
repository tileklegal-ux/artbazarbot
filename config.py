import os

# === Базовые настройки бота ===

# Токен бота из переменных окружения Fly.io
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    # Лучше упасть при старте, чем молча не работать
    raise RuntimeError("BOT_TOKEN is not set in environment")


# === Webhook / Fly.io ===
# Имя приложения на Fly.io: artbazarbot  →  https://artbazarbot.fly.dev
# Можно переопределить APP_URL через переменную окружения APP_URL, если нужно.
APP_URL = os.getenv("APP_URL", "https://artbazarbot.fly.dev").rstrip("/")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"


# === База данных ===
# В простом варианте — один файл в корне контейнера
DB_PATH = os.getenv("DB_PATH", "database.db")


# === Роли и контакты ===
# Владелец и основной менеджер по ТЗ
OWNER_ID = int(os.getenv("OWNER_ID", "1974482384"))
MANAGER_ID = int(os.getenv("MANAGER_ID", "571499876"))

OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@ihaariss")
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "@Artbazar_support")


# === OpenAI ===
# Ключ и модель, если где-то понадобится из конфига
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
