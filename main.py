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

# ===== МОДУЛИ =====
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

OWNER_ID = 8389875803  # ← вставлен твой Telegram ID


# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Основная таблица пользователей
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',
            lang TEXT NOT NULL DEFAULT 'ru',
            premium_until INTEGER,
            created_at INTEGER,
            last_active INTEGER,
            total_requests INTEGER DEFAULT 0
        )
    """)

    # Миграции под новые поля (если старые данные)
    def add_column(name, col_type):
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {name} {col_type}")
        except:
            pass

    add_column("username", "TEXT")
    add_column("first_name", "TEXT")
    add_column("role", "TEXT DEFAULT 'user'")
    add_column("premium_until", "INTEGER")
    add_column("created_at", "INTEGER")
    add_column("last_active", "INTEGER")
    add_column("total_requests", "INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


# ===== РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ =====
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


# ===== НАЗНАЧАЕМ ВЛАДЕЛЬЦА =====
def make_owner(owner_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET role='owner' WHERE user_id=?", (owner_id,))
    conn.commit()
    conn.close()


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
        "btn_change_lang": "🌐 Сменить язык",
        "btn_back": "‹ Назад",
        "ask_product": "Введите название товара:",
        "unknown_cmd": "Функция пока не подключена.",
    },
}

# Кыргызстан
LOCALES["kg"] = {
    "choose_lang": "Тилди тандаңыз:",
    "menu_title": "Башкы меню:",
    "btn_analyze": "🔍 Товар анализи",
    "btn_trends": "📊 Тренддер",
    "btn_ideas": "💡 Идеялар",
    "btn_categories": "🛒 Категориялар",
    "btn_calc": "🧮 Пайда эсептегич",
    "btn_desc": "✍️ Саттуу тексти",
    "btn_premium": "⭐ Премиум аналитика",
    "btn_change_lang": "🌐 Тилди өзгөртүү",
    "btn_back": "‹ Артка",
    "ask_product": "Товар атын жазыңыз:",
    "unknown_cmd": "Функция азырынча иштебейт.",
}

# Казахстан
LOCALES["kz"] = {
    "choose_lang": "Тілді таңдаңыз:",
    "menu_title": "Басты мәзір:",
    "btn_analyze": "🔍 Тауар талдауы",
    "btn_trends": "📊 Трендтер",
    "btn_ideas": "💡 Идеялар",
    "btn_categories": "🛒 Категориялар",
    "btn_calc": "🧮 Пайда калькуляторы",
    "btn_desc": "✍️ Сату мәтіні",
    "btn_premium": "⭐ Премиум аналитика",
    "btn_change_lang": "🌐 Тілді ауыстыру",
    "btn_back": "‹ Артқа",
    "ask_product": "Тауар атын енгізіңіз:",
    "unknown_cmd": "Бұл функция әлі іске қосылған жоқ.",
}


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_lang(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] in LOCALES else "ru"


def set_lang(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()


def increment_requests(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ===== КЛАВИАТУРЫ =====
def get_main_keyboard(lang):
    t = LOCALES[lang]
    return ReplyKeyboardMarkup([
        [t["btn_analyze"]],
        [t["btn_trends"], t["btn_ideas"]],
        [t["btn_categories"]],
        [t["btn_calc"], t["btn_desc"]],
        [t["btn_premium"]],
        [t["btn_change_lang"]],
    ], resize_keyboard=True)


def get_back_keyboard(lang):
    return ReplyKeyboardMarkup([[LOCALES[lang]["btn_back"]]], resize_keyboard=True)


def get_language_keyboard():
    return ReplyKeyboardMarkup([
        ["🇰🇬 Кыргызча", "🇰🇿 Қазақша"],
        ["🇷🇺 Русский"],
    ], resize_keyboard=True)


# ===== ОБРАБОТЧИКИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)

    if user.id == OWNER_ID:
        make_owner(user.id)

    set_lang(user.id, "ru")

    await update.message.reply_text(
        LOCALES["ru"]["choose_lang"],
        reply_markup=get_language_keyboard()
    )


async def handle_language_choice(update: Update, context):
    user_id = update.effective_user.id
    txt = update.message.text.lower()

    if "кыргыз" in txt:
        lang = "kg"
    elif "қазақ" in txt or "казақ" in txt:
        lang = "kz"
    else:
        lang = "ru"

    set_lang(user_id, lang)

    await update.message.reply_text(
        LOCALES[lang]["menu_title"],
        reply_markup=get_main_keyboard(lang)
    )


async def handle_buttons(update: Update, context):
    user = update.effective_user
    user_id = user.id
    lang = get_lang(user_id)
    t = LOCALES[lang]
    text = update.message.text

    increment_requests(user_id)

    # Назад
    if text == t["btn_back"]:
        context.user_data["mode"] = None
        await update.message.reply_text(t["menu_title"], reply_markup=get_main_keyboard(lang))
        return

    # Смена языка
    if text == t["btn_change_lang"]:
        await update.message.reply_text(t["choose_lang"], reply_markup=get_language_keyboard())
        return

    # Анализ товара
    if text == t["btn_analyze"]:
        context.user_data["mode"] = "analyze"
        await update.message.reply_text(t["ask_product"], reply_markup=get_back_keyboard(lang))
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

    # Калькулятор
    if text == t["btn_calc"]:
        await update.message.reply_text(calculate_profit("data", lang))
        return

    # Описание
    if text == t["btn_desc"]:
        context.user_data["mode"] = "description"
        await update.message.reply_text(t["ask_product"], reply_markup=get_back_keyboard(lang))
        return

    # Премиум
    if text == t["btn_premium"]:
        await update.message.reply_text(premium_info(lang))
        return

    # Ввод товара для анализа
    if context.user_data.get("mode") == "analyze":
        context.user_data["mode"] = None
        await update.message.reply_text(
            analyze_product(text, lang),
            reply_markup=get_main_keyboard(lang)
        )
        return

    # Ввод товара для описания
    if context.user_data.get("mode") == "description":
        context.user_data["mode"] = None
        await update.message.reply_text(
            generate_description(text, lang),
            reply_markup=get_main_keyboard(lang)
        )
        return

    # Остальное
    await update.message.reply_text(t["unknown_cmd"], reply_markup=get_main_keyboard(lang))


# ===== MAIN =====
def main():
    init_db()
    make_owner(OWNER_ID)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Кыргызча|Қазақша|Русский"), handle_language_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
