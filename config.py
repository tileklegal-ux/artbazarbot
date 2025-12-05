import os
from dotenv import load_dotenv

# Загружаем переменные из .env, если файл существует (для локального тестирования)
load_dotenv()

# Основные токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Переменные для Webhook (ОБЯЗАТЕЛЬНО для Fly.io)
# Они должны быть установлены как Secrets на Fly.io!
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST") # Например, artbazarbot.fly.dev
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH") # Например, /super_secret_artbazar_path_999

# Формируем полный URL для Webhook
if WEBHOOK_HOST and WEBHOOK_PATH:
    # Fly.io использует HTTPS
    WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
else:
    # Если переменные не установлены, это критическая ошибка
    WEBHOOK_URL = None
    if os.getenv("FLY_APP_NAME"):
        raise ValueError("CRITICAL ERROR: WEBHOOK_HOST or WEBHOOK_PATH environment variables are missing.")

# Также проверяем, что BOT_TOKEN установлен
if not BOT_TOKEN:
    raise ValueError("CRITICAL ERROR: BOT_TOKEN environment variable is missing.")
