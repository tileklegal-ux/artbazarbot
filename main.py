import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN
from handlers import router
from database import init_db


WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://artbazarbot.fly.dev/webhook")
WEBHOOK_PATH = "/webhook"


async def on_startup(app: web.Application):
    bot: Bot = app["bot"]
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    bot: Bot = app["bot"]
    await bot.delete_webhook()
    await bot.session.close()
    print("Webhook deleted and bot session closed")


async def create_app() -> web.Application:
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app["bot"] = bot

    SimpleRequestHandler(dp, bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    web.run_app(create_app(), host="0.0.0.0", port=port)
