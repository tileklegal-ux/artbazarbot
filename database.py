import aiosqlite
import logging
import os

# ----------------------------------------------------------------------
# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ДЛЯ FLY.IO:
# Указываем, что база данных должна храниться в папке /app/data, 
# которая будет подключена к постоянному хранилищу (Volume).
# ----------------------------------------------------------------------
DATABASE_DIR = "/app/data"
DATABASE_NAME = os.path.join(DATABASE_DIR, "artbazar_db.sqlite")

async def init_db():
    """Инициализирует базу данных, создавая таблицу пользователей, если ее нет."""
    try:
        # Убеждаемся, что директория для Volume существует
        if not os.path.exists(DATABASE_DIR):
            os.makedirs(DATABASE_DIR, exist_ok=True)
            logging.info(f"Директория {DATABASE_DIR} была создана.")
        
        # Подключение к базе данных в постоянной локации
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
        # Если здесь ошибка, это проблема с Fly.io Volume!
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: Ошибка инициализации базы данных. Проверьте Volume и fly.toml: {e}")

async def get_user_language(user_id):
    """Получает код языка пользователя. По умолчанию возвращает 'ru'."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute("SELECT language_code FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                await set_user_language(user_id, 'ru')
                return 'ru'
    except Exception as e:
        logging.error(f"Ошибка при получении языка пользователя {user_id}: {e}")
        return 'ru'

async def set_user_language(user_id, lang_code):
    """Устанавливает или обновляет код языка пользователя."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, language_code) VALUES (?, ?)",
                (user_id, lang_code)
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при установке языка пользователя {user_id}: {e}")
