import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router
from database import init_db  # ← ВАЖНО: добавили


logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    # создаём таблицы БД (users)
    init_db()

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

    # 1) Telegram прислал JSON
    data = await request.json()

    # 2) Превращаем JSON в объект Update (важно!)
    update = Update.model_validate(data)

    # 3) Передаём обновление в aiogram
    await dp.feed_update(bot, update)

    # 4) Отвечаем Telegram "OK" (обязательно)
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан!")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # создаём aiohttp веб-сервер
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    # стартовые действия
    await on_startup(bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=8080
    )
    await site.start()

    logging.info("💡 BOT RUNNING VIA WEBHOOK on 0.0.0.0:8080")

    try:
        # держим контейнер живым
        await asyncio.Event().wait()
    finally:
        await on_shutdown(bot)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
