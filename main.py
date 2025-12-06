import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router as user_router
from admin_panel import router as admin_router
from database import init_db
from roles_db import init_roles_table
from premium_db import init_premium_table
from usage_db import init_usage_table

logging.basicConfig(level=logging.INFO)


async def handle(request: web.Request) -> web.Response:
    """
    Основной обработчик вебхука: принимает апдейт от Telegram
    и передаёт его в aiogram.
    """
    data = await request.json()
    update = Update.model_validate(data)

    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    await dp.feed_update(bot, update)
    return web.Response()


async def on_startup(app: web.Application):
    """
    Старт приложения:
    - настраиваем вебхук
    - инициализируем БД
    """
    bot: Bot = app["bot"]

    # Настройка вебхука
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

    # Таблицы БД
    init_db()
    init_roles_table()
    init_premium_table()
    init_usage_table()
    logging.info("Database tables initialized")


async def on_shutdown(app: web.Application):
    """
    Корректное завершение:
    - удаляем вебхук
    - закрываем сессию бота
    """
    bot: Bot = app["bot"]

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    logging.info("Bot webhook deleted and session closed")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    # Бот и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Роутеры: пользовательский + админка
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # aiohttp-приложение
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    # Маршрут вебхука
    app.router.add_post(WEBHOOK_PATH, handle)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Запуск HTTP-сервера на 0.0.0.0:8080 (под Fly.io)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logging.info("💡 BOT RUNNING VIA WEBHOOK on 0.0.0.0:8080")

    try:
        # держим процесс живым
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
