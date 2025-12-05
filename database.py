import aiosqlite
import logging

# Имя файла базы данных. Он будет храниться в Fly Volume.
DATABASE_NAME = "artbazar_db.sqlite"

async def init_db():
    """Инициализирует базу данных, создавая таблицу 'users', если ее нет."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language_code TEXT DEFAULT 'ru'
                )
            """)
            await db.commit()
        logging.info("База данных успешно инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")

async def get_user_language(user_id):
    """Получает код языка пользователя. По умолчанию возвращает 'ru'."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT language_code FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            # Если пользователь новый, создаем его с языком по умолчанию
            await set_user_language(user_id, 'ru')
            return 'ru'

async def set_user_language(user_id, lang_code):
    """Устанавливает или обновляет код языка пользователя."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # INSERT OR REPLACE позволяет либо создать новую запись, либо обновить существующую.
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, language_code) VALUES (?, ?)",
            (user_id, lang_code)
        )
        await db.commit()
