import os

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Вебхук (должен совпадать с тем, что в Fly)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/") + WEBHOOK_PATH

# БД
DB_PATH = os.getenv("DB_PATH", "database.db")

# Владелец по умолчанию (первичный OWNER, записываем в БД при старте)
# ← сюда ставим твой Telegram ID
OWNER_ID = int(os.getenv("OWNER_ID", "1974482384"))

# (опционально) дефолтный менеджер — можно не использовать
DEFAULT_MANAGER_ID = os.getenv("DEFAULT_MANAGER_ID")
