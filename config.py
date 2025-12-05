import os

# ==========================
# 🔐 Токены
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Если не задан — берем модель по умолчанию
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ==========================
# 🌐 Webhook настройки (для Fly.io)
# ==========================

# Твой домен на Fly.io (менять только если другое приложение)
WEBHOOK_HOST = "https://artbazarbot.fly.dev"

# путь, по которому Fly.io принимает webhook
WEBHOOK_PATH = "/webhook"

# Полный URL, который Telegram будет дергать
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH


# ==========================
# 🛑 Проверки перед запуском
# ==========================

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не задан! Проверь секреты Fly.io")

if not OPENAI_API_KEY:
    print("⚠️ ВНИМАНИЕ: OPENAI_API_KEY не задан. AI функции отключены.")
