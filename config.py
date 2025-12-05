import os
from dotenv import load_dotenv

# Загрузка .env (для локального тестирования, на Fly.io не используется)
load_dotenv()

# Обязательные переменные, которые Fly.io должен установить как Secrets
# BOT_TOKEN: Ваш токен от BotFather (fly secrets set BOT_TOKEN='...')
BOT_TOKEN = os.getenv("BOT_TOKEN")

# WEBHOOK_HOST: Имя вашего приложения на Fly.io (например, artbazarbot)
# Он нужен, чтобы main.py мог сформировать полный WEBHOOK_URL
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")

# Ключ OpenAI (если вы его установите)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка наличия токена
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен. Установите его как Secret.")
