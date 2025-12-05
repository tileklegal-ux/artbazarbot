import asyncio
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

from config import BOT_TOKEN
from handlers import router

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # webhook config
    webhook_path = os.getenv("WEBHOOK_PATH")
    webhook_url = os.getenv("WEBHOOK_URL")

    # создаём Aiohttp app
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, path=webhook_path)
    setup_application(app, dp)

    # устанавливаем webhook
    await bot.set_webhook(webhook_url)

    # стартуем сервер
    port = int(os.getenv("PORT", 8080))
    return app


if __name__ == "__main__":
    web.run_app(main(), host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
