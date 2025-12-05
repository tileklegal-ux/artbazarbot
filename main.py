import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db
from handlers import register_handlers

BOT_TOKEN = "твoй_бот_токен_сюда"


async def main():
    # Инициализация базы
    init_db()

    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация всех хендлеров
    register_handlers(dp)

    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
