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

# ===== ИМПОРТ МОДУЛЕЙ =====
from analytics import analyze_product
from trends import get_trends
from ideas import get_ideas
from categories import get_categories
from profit_calc import calculate_profit
from descriptions import generate_description
from premium import premium_info

# ===== КОНФИГ =====
TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "database.db"

# ===== ЯЗЫКОВЫЕ ПАКЕТЫ =====
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
        "ask_product": "Введите название товара:",
        "unknown_cmd": "Функция пока не подключена.",
    },
    "kg": {
        "choose_lang": "Тилди тандаңыз:",
        "menu_title": "Башкы меню:",
        "btn_analyze": "🔍 Товар анализи",
        "btn_trends": "📊 Тренддер",
        "btn_ideas": "💡 Идеялар",
        "btn_categories": "🛒 Категориялар",
        "btn_calc": "🧮 Пайда эсептегич",
        "btn_desc": "✍️ Саттуу тексти",
        "btn_premium": "⭐ Премиум аналитика",
        "ask_product": "Товар атын жазыңыз:",
        "unknown_cmd": "Функция азырынча иштебейт.",
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
        "ask_product": "Тауар атын енгізіңіз:",
        "unknown_cmd": "Бұл функция әлі іске қосылған жоқ.",
    },
}

# ===== БАЗА ДАННЫХ =====
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
    return "ru"


# ===== КЛАВИАТУРЫ =====
def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    t = LOCALES[lang]
    keyboard = [
        [t["btn_analyze"]],
        [t["btn_trends"], t["btn_ideas"]],
        [t["btn_categories"]],
        [t["btn_calc"], t["btn_desc"]],
        [t["btn_premium"]],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["🇰🇬 Кыргызча", "🇰🇿 Қазақша"], ["🇷🇺 Русский"]],
        resize_keyboard=True
    )


# ===== ЛОГИКА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_lang(user_id, "ru")

    await update.message.reply_text(
        LOCALES["ru"]["choose_lang"],
        reply_markup=get_language_keyboard()
    )


async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

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
        reply_markup=get_main_keyboard(lang)
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    t = LOCALES[lang]
    text = update.message.text

    # Анализ товара → запрос названия товара
    if text == t["btn_analyze"]:
        await update.message.reply_text(t["ask_product"])
        context.user_data["mode"] = "analyze"
        return

    # Тренды
    if text == t["btn_trends"]:
        await update.message.reply_text(get_trends(lang))
        return

    # Идеи
    if text == t["btn_ideas"]:
        await update.message.reply_text(get_ideas(lang))
        return

    # Категории
    if text == t["btn_categories"]:
        await update.message.reply_text(get_categories(lang))
        return

    # Калькулятор прибыли
    if text == t["btn_calc"]:
        await update.message.reply_text(calculate_profit("data", lang))
        return

    # Описание для продажи
    if text == t["btn_desc"]:
        await update.message.reply_text(t["ask_product"])
        context.user_data["mode"] = "description"
        return

    # Премиум аналитика
    if text == t["btn_premium"]:
        await update.message.reply_text(premium_info(lang))
        return

    # Если пользователь вводит название для анализа
    if context.user_data.get("mode") == "analyze":
        context.user_data["mode"] = None
        await update.message.reply_text(analyze_product(text, lang))
        return

    # Название для описания
    if context.user_data.get("mode") == "description":
        context.user_data["mode"] = None
        await update.message.reply_text(generate_description(text, lang))
        return

    # Остальное
    await update.message.reply_text(
        t["unknown_cmd"],
        reply_markup=get_main_keyboard(lang)
    )


# ===== MAIN =====
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Кыргызча|Қазақша|Русский"), handle_language_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
