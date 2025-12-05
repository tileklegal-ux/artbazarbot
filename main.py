# main.py

import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db
from handlers import router


async def main():
    init_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Bot started…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
