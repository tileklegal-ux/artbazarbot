import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH # Импортируем URL и PATH
from handlers import router
from database import init_db

# Убедимся, что логирование включено
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Инициализируем базу данных (теперь она в /app/data и работает)
    # Примечание: init_db должен быть асинхронным, как в моей последней версии database.py
    await init_db()

    # 2. Инициализируем бота и диспетчер
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # 3. Настраиваем Webhook
    # Сначала удаляем все старые вебхуки, чтобы избежать конфликтов
    await bot.delete_webhook(drop_pending_updates=True)

    # Устанавливаем новый Webhook URL
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=dp.resolve_used_update_types())
    
    # 4. Запускаем Webhook сервер на порту 8080 и адресе 0.0.0.0
    # Fly.io требует, чтобы Webhook слушал внутренний порт 8080
    logging.info(f"Starting Webhook on port 8080 and path {WEBHOOK_PATH}...")
    await dp.start_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_path=WEBHOOK_PATH,
        bot=bot
    )

if __name__ == "__main__":
    try:
        # aiogram 3 требует асинхронного запуска
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
    except Exception as e:
        logging.error(f"Critical error during startup: {e}")
