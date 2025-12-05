import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, OWNER_ID
from handlers import router as user_router
from admin_panel import router as admin_router
from database import init_db
from premium_db import init_premium_table
from roles_db import init_roles_table

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    # Инициализация БД
    init_db()
    init_premium_table()
    init_roles_table()  # запишет OWNER_ID как владельца

    # ставим webhook в Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"🚀 WEBHOOK установлен: {WEBHOOK_URL} (OWNER_ID={OWNER_ID})")


async def on_shutdown(bot: Bot):
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

    # Роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # aiohttp-приложение
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    # стартовые действия
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
