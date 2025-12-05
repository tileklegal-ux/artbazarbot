import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

WEBHOOK_HOST = "https://artbazarbot.fly.dev"
WEBHOOK_PATH = "/webhook"

# 🔥 ЭТОГО У ТЕБЯ НЕ ХВАТАЛО
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Проверь Secrets Fly.io")

if not OPENAI_API_KEY:
    print("⚠️ ВНИМАНИЕ: OPENAI_API_KEY не задан. AI отключён.")
