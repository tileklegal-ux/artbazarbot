import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router


logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    # ставим webhook в Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"🚀 WEBHOOK установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    # снимаем webhook при аккуратной остановке контейнера
    await bot.delete_webhook()
    logging.info("🛑 WEBHOOK удалён")


async def webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    # ❶ читаем JSON
    data = await request.json()
    # ❷ превращаем его в объект Update — ЭТО то, чего не хватало
    update = Update.model_validate(data)

    # ❸ отправляем апдейт в aiogram
    await dp.feed_update(bot, update)

    # ❹ отвечаем Telegram'у 200 OK
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан (env BOT_TOKEN)")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # HTTP-сервер для webhook
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    # принимаем POST по /webhook
    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    # ставим webhook в Telegram
    await on_startup(bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
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
