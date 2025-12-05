import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router
from admin_panel import router_admin        # ← ДОБАВЛЕНО
from database import init_db                # ← уже есть
from premium_db import init_premium_table   # ← ДОБАВЛЕНО


logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    # создаём таблицы БД (users и premium)
    init_db()
    init_premium_table()   # ← создаём таблицу премиума

    # ставим webhook в Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"🚀 WEBHOOK установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    # снимаем webhook
    await bot.delete_webhook()
    logging.info("🛑 WEBHOOK удалён")


async def webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    data = await request.json()
    update = Update.model_validate(data)

    await dp.feed_update(bot, update)
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан!")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # подключаем роутеры
    dp.include_router(router)        # пользовательские хендлеры
    dp.include_router(router_admin)  # админ-панель ← ДОБАВЛЕНО

    # создаём aiohttp веб-сервер
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    # старт
    await on_startup(bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    logging.info("💡 BOT RUNNING VIA WEBHOOK on 0.0.0.0:8080")

    try:
        await asyncio.Event().wait()
    finally:
        await on_shutdown(bot)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
