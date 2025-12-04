import os
import time
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "database.db"

OWNER_ID = 8389875803  # ТИЛЕК — владелец бота


# ==========================
#     БАЗА ДАННЫХ
# ==========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # базовая таблица пользователей
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',
            lang TEXT DEFAULT 'ru',
            premium_until INTEGER,
            created_at INTEGER,
            last_active INTEGER,
            total_requests INTEGER DEFAULT 0
        )
    """)

    # миграции (если бот обновляется — не ломает старые данные)
    def add_col(name, type):
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {name} {type}")
        except:
            pass

    add_col("username", "TEXT")
    add_col("first_name", "TEXT")
    add_col("role", "TEXT DEFAULT 'user'")
    add_col("premium_until", "INTEGER")
    add_col("created_at", "INTEGER")
    add_col("last_active", "INTEGER")
    add_col("total_requests", "INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


def register_user(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT INTO users (user_id, username, first_name, created_at, last_active)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_active = excluded.last_active
    """, (
        user.id,
        user.username,
        user.first_name,
        int(time.time()),
        int(time.time())
    ))

    conn.commit()
    conn.close()


def set_role(user_id, role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    conn.commit()
    conn.close()


def get_role(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "user"


def increment_requests(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ==========================
#        ЯЗЫКИ
# ==========================
LOCALES = {
    "ru": {
        "choose_lang": "Выберите язык:",
        "menu": "Главное меню:",
        "btn_analyze": "🔍 Анализ товара (демо)",
        "btn_trends": "📊 Тренды (демо)",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_cabinet": "📂 Мой кабинет",
        "btn_back": "‹ Назад",
    },

    "kg": {
        "choose_lang": "Тилди тандаңыз:",
        "menu": "Башкы меню:",
        "btn_analyze": "🔍 Товар анализи (демо)",
        "btn_trends": "📊 Тренддер (демо)",
        "btn_change_lang": "🌐 Тилди өзгөртүү",
        "btn_cabinet": "📂 Менин кабинетим",
        "btn_back": "‹ Артка",
    },

    "kz": {
        "choose_lang": "Тілді таңдаңыз:",
        "menu": "Басты мәзір:",
        "btn_analyze": "🔍 Тауар талдауы (демо)",
        "btn_trends": "📊 Трендтер (демо)",
        "btn_change_lang": "🌐 Тілді ауыстыру",
        "btn_cabinet": "📂 Жеке кабинет",
        "btn_back": "‹ Артқа",
    },
}


def get_lang(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "ru"


def set_lang(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()


# ==========================
#      КЛАВИАТУРЫ
# ==========================
def keyboard_main(lang):
    t = LOCALES[lang]
    return ReplyKeyboardMarkup([
        [t["btn_analyze"]],
        [t["btn_trends"]],
        [t["btn_cabinet"]],
        [t["btn_change_lang"]],
    ], resize_keyboard=True)


def keyboard_lang():
    return ReplyKeyboardMarkup([
        ["🇰🇬 Кыргызча", "🇰🇿 Қазақша"],
        ["🇷🇺 Русский"],
    ], resize_keyboard=True)


# ==========================
#       ХЕНДЛЕРЫ
# ==========================
async def start(update: Update, context):
    user = update.effective_user
    register_user(user)

    if user.id == OWNER_ID:
        set_role(user.id, "owner")

    await update.message.reply_text(
        LOCALES["ru"]["choose_lang"],
        reply_markup=keyboard_lang()
    )


async def choose_lang(update: Update, context):
    user_id = update.effective_user.id
    txt = update.message.text.lower()

    if "кыргыз" in txt:
        lang = "kg"
    elif "қазақ" in txt:
        lang = "kz"
    else:
        lang = "ru"

    set_lang(user_id, lang)

    t = LOCALES[lang]

    await update.message.reply_text(
        t["menu"],
        reply_markup=keyboard_main(lang)
    )


async def handle(update: Update, context):
    user_id = update.effective_user.id
    user = update.effective_user

    increment_requests(user_id)

    lang = get_lang(user_id)
    t = LOCALES[lang]
    text = update.message.text

    # демо-функции
    if text == t["btn_analyze"]:
        await update.message.reply_text("🔍 Демо-анализ работает!")
        return

    if text == t["btn_trends"]:
        await update.message.reply_text("📊 Демо тренды работают!")
        return

    # личный кабинет (заглушка)
    if text == t["btn_cabinet"]:
        await update.message.reply_text(f"""
📂 Ваш кабинет

ID: {user_id}
Username: @{user.username}
Роль: {get_role(user_id)}
Запросов: обновляется...
Премиум: скоро
""")
        return

    if text == t["btn_change_lang"]:
        await update.message.reply_text(t["choose_lang"], reply_markup=keyboard_lang())
        return

    await update.message.reply_text("Команда пока не поддерживается.")


# ==========================
#          MAIN
# ==========================
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Кыргызча|Қазақша|Русский"), choose_lang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
