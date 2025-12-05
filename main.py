import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_PATH
from handlers import router


# --------------------------
#  Создание приложения
# --------------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)


# --------------------------
#  Обработчик webhook
# --------------------------

async def handle_webhook(request):
    update_data = await request.json()
    await dp.feed_raw_update(bot, update_data)
    return web.Response(text="OK")


# --------------------------
#  Старт приложения
# --------------------------

async def on_startup(app):
    webhook_url = WEBHOOK_HOST + WEBHOOK_PATH

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url)

    print(f"Webhook установлен: {webhook_url}")


async def on_shutdown(app):
    await bot.session.close()
    print("Bot session closed")


# --------------------------
#  Запуск веб-сервера
# --------------------------

def create_app():
    app = web.Application()
    app.add_routes([web.post(WEBHOOK_PATH, handle_webhook)])

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


# --------------------------
#  Точка входа
# --------------------------

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
