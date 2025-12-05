import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from handlers import router


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"🚀 WEBHOOK установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("🛑 WEBHOOK удалён")


async def webhook_handler(request):
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]
    update = await request.json()
    await dp.feed_update(bot, update)
    return web.Response(text="OK")


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # HTTP сервер
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp

    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    await on_startup(bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    print("💡 BOT RUNNING VIA WEBHOOK...")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
