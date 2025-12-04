import os
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

# ----- ЯЗЫКОВЫЕ ПАКЕТЫ -----
LOCALES = {
    "ru": {
        "choose_lang": "Выберите язык:",
        "menu_title": "Главное меню:",
        "btn_analyze": "🔍 Анализ товара",
        "btn_trends": "📊 Тренды",
        "btn_ideas": "💡 Идеи",
        "btn_categories": "🛒 Категории",
        "btn_calc": "🧮 Калькулятор прибыли",
        "btn_desc": "✍️ Описание для продажи",
        "btn_premium": "⭐ Премиум аналитика",
        "unknown_cmd": "Пока я умею только выбирать язык и показывать меню. Остальные функции подключим поэтапно.",
    },
    "kg": {
        "choose_lang": "Тилди тандаңыз:",
        "menu_title": "Башкы меню:",
        "btn_analyze": "🔍 Товар анализи",
        "btn_trends": "📊 Тренддер",
        "btn_ideas": "💡 Идеялар",
        "btn_categories": "🛒 Категориялар",
        "btn_calc": "🧮 Пайда эсептегич",
        "btn_desc": "✍️ Сатуу тексти",
        "btn_premium": "⭐ Премиум аналитика",
        "unknown_cmd": "Азырынча мен тилди тандоону жана менюну гана көрсөтөм. Калган функцияларды акырындык менен кошобуз.",
    },
    "kz": {
        "choose_lang": "Тілді таңдаңыз:",
        "menu_title": "Басты мәзір:",
        "btn_analyze": "🔍 Тауар талдауы",
        "btn_trends": "📊 Трендтер",
        "btn_ideas": "💡 Идеялар",
        "btn_categories": "🛒 Категориялар",
        "btn_calc": "🧮 Пайда калькуляторы",
        "btn_desc": "✍️ Сату мәтіні",
        "btn_premium": "⭐ Премиум аналитика",
        "unknown_cmd": "Әзірге мен тек тілді таңдау және мәзір көрсетуді білемін. Қалған функцияларды кезең-кезеңімен қосамыз.",
    },
}


# ----- БАЗА ДАННЫХ (SQLite) -----
def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL DEFAULT 'ru'
        )
        """
    )
    conn.commit()
    conn.close()


def set_lang(user_id: int, lang: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO users (user_id, lang)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang
        """,
        (user_id, lang),
    )
    conn.commit()
    conn.close()


def get_lang(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0] in LOCALES:
        return row[0]
    return "ru"  # по умолчанию русский


# ----- КЛАВИАТУРЫ -----
def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    t = LOCALES.get(lang, LOCALES["ru"])
    keyboard = [
        [t["btn_analyze"]],
        [t["btn_trends"], t["btn_ideas"]],
        [t["btn_categories"]],
        [t["btn_calc"], t["btn_desc"]],
        [t["btn_premium"]],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_language_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🇰🇬 Кыргызча", "🇰🇿 Қазақша"],
        ["🇷🇺 Русский"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ----- ХЕНДЛЕРЫ -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    # сразу регистрируем юзера с русским по умолчанию
    set_lang(user_id, "ru")

    await update.message.reply_text(
        LOCALES["ru"]["choose_lang"],
        reply_markup=get_language_keyboard(),
    )


async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    text = (update.message.text or "").lower()

    if "кыргыз" in text:
        lang = "kg"
    elif "қазақ" in text or "казақ" in text:
        lang = "kz"
    else:
        lang = "ru"

    set_lang(user_id, lang)

    t = LOCALES[lang]
    await update.message.reply_text(
        t["menu_title"],
        reply_markup=get_main_keyboard(lang),
    )


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    t = LOCALES[lang]

    await update.message.reply_text(
        t["unknown_cmd"],
        reply_markup=get_main_keyboard(lang),
    )


def main() -> None:
    init_db()

    app = Application.builder().token(TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # выбор языка
    app.add_handler(
        MessageHandler(
            filters.Regex("Кыргызча|Қазақша|Русский"),
            handle_language_choice,
        )
    )

    # все остальное пока ловим как "пока не реализовано"
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    app.run_polling()


if __name__ == "__main__":
    main()
