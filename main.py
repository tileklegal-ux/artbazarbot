import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router # Роутер с нашей логикой
from database import init_db # Инициализация БД
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Порт, который должен слушать веб-сервер (обязательно 8080 для Fly.io)
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8080

async def on_startup(bot: Bot):
    """Действия при запуске: инициализация БД и установка Webhook."""
    
    # 1. Инициализация базы данных
    await init_db()
    
    # 2. Установка Webhook
    logging.info(f"Установка Webhook на URL: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)
    
    # 3. Приветственное сообщение
    bot_info = await bot.get_me()
    logging.info(f"Бот запущен: @{bot_info.username}")

async def on_shutdown(bot: Bot):
    """Действия при остановке: удаление Webhook."""
    logging.info("Удаление Webhook.")
    await bot.delete_webhook()
    logging.info("Бот остановлен.")


def main():
    """Основная функция для запуска Webhook-сервера."""
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Добавление роутера с нашей логикой
    dp.include_router(router)
    
    # Настройка хэндлеров запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # 1. Создание приложения aiohttp
    app = web.Application()
    
    # 2. Настройка обработчика запросов Webhook
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    # 3. Привязка обработчика к нужному пути (/super_secret_artbazar_path_999)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # 4. Настройка приложения aiohttp для диспетчера
    setup_application(app, dp, bot=bot)

    # 5. Запуск веб-сервера aiohttp, слушающего порт 8080
    web.run_app(
        app, 
        host=WEB_SERVER_HOST, 
        port=WEB_SERVER_PORT
    )

if __name__ == "__main__":
    main()
