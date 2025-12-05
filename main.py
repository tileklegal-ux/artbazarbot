import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN
from handlers import router
from database import init_db

async def on_startup(bot: Bot, webhook_url: str):
    await bot.set_webhook(webhook_url)

async def create_app():
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()

    SimpleRequestHandler(dp, bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    app.on_startup.append(lambda _: on_startup(bot, "https://artbazarbot.fly.dev/webhook"))
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
