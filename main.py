import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router as user_router
from admin_panel import router as admin_router  # если admin_panel есть
from database import init_db
from premium_db import init_premium_table
from roles_db import init_roles_table
from usage_db import init_usage_table


logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    # Инициализация всех таблиц в одной точке
    init_db()
    init_roles_table()
    init_premium_table()
    init_usage_table()

    # Ставим webhook в Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"🚀 WEBHOOK установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    # Снимаем webhook при остановке
    await bot.delete_webhook()
    logging.info("🛑 WEBHOOK удалён")


async def webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    # 1) Telegram прислал JSON
    data = await request.json()

    # 2) Превращаем JSON в объект Update
    update = Update.model_validate(data)

    # 3) Передаём обновление в aiogram
    await dp.feed_update(bot, update)

    # 4) Отвечаем Telegram "OK"
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан!")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # HTTP-сервер для webhook
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    # Стартовые действия
    await on_startup(bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=8080,
    )
    await site.start()

    logging.info("💡 BOT RUNNING VIA WEBHOOK on 0.0.0.0:8080")

    try:
        # Держим контейнер живым
        await asyncio.Event().wait()
    finally:
        await on_shutdown(bot)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
