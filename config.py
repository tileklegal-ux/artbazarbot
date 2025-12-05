import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Модель OpenAI по умолчанию
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Проверь секреты на Fly.io")

if not OPENAI_API_KEY:
    # Бот сможет жить без OpenAI, но это твоя фишка — так что лучше задать
    print("ВНИМАНИЕ: OPENAI_API_KEY не задан. AI-функции работать не будут.")
