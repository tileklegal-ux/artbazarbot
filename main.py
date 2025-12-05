import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import BOT_TOKEN
from handlers import router
from database import init_db

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def on_startup(app):
    """Действия при старте сервера"""
    # Достаем бота из приложения
    bot = app['bot']
    
    # Получаем URL вебхука из переменных окружения
    webhook_url = os.getenv("WEBHOOK_URL")
    
    # 1. Инициализируем БД
    await init_db()
    
    # 2. Устанавливаем Webhook
    if webhook_url:
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook установлен на: {webhook_url}")
    else:
        logging.error("WEBHOOK_URL не найден в переменных окружения!")

async def on_shutdown(app):
    """Действия при остановке сервера"""
    bot = app['bot']
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("Webhook удален, сессия бота закрыта.")

def create_app():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Создаем aiohttp приложение
    app = web.Application()
    app['bot'] = bot # Сохраняем ссылку на бота в приложении

    # Получаем путь вебхука (по умолчанию /webhook)
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    
    # Регистрируем обработчик вебхука
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=webhook_path)
    
    # Настраиваем приложение aiogram
    setup_application(app, dp, bot=bot)
    
    # Регистрируем сигналы (что делать при старте и стопе)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app

if __name__ == "__main__":
    # Получаем порт от Fly.io (по умолчанию 8080)
    port = int(os.getenv("PORT", 8080))
    
    # Запускаем приложение
    # web.run_app сам создаст цикл событий, не нужно использовать asyncio.run
    web.run_app(create_app(), host="0.0.0.0", port=port)
