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

# BOT CONFIG
TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "database.db"

OWNER_ID = 8389875803  # ТИЛЕК — владелец
MANAGER_USERNAME = "Artbazar_support"  # менеджер для проверки чеков


# ==========================
#          БАЗА ДАННЫХ
# ==========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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

    # миграции — делаем базу устойчивой
    def add_col(name, type_):
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {name} {type_}")
        except:
            pass

    add_col("premium_until", "INTEGER")
    add_col("role", "TEXT DEFAULT 'user'")
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


def increment_requests(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def set_premium(user_id, days):
    premium_until = int(time.time()) + days * 24 * 3600
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET premium_until=? WHERE user_id=?", (premium_until, user_id))
    conn.commit()
    conn.close()
    return premium_until


def get_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT user_id, username, first_name, role, lang,
               premium_until, created_at, last_active, total_requests
        FROM users WHERE user_id=?
    """, (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "role": row[3],
        "lang": row[4],
        "premium_until": row[5],
        "created_at": row[6],
        "last_active": row[7],
        "total_requests": row[8],
    }


# ==========================
#        ЯЗЫКИ
# ==========================
LOCALES = {
    "ru": {
        "choose_lang": "Выберите язык:",
        "menu": "Главное меню:",
        "btn_analyze": "🔍 Анализ товара (демо)",
        "btn_trends": "📊 Тренды (демо)",
        "btn_cabinet": "📂 Мой кабинет",
        "btn_buy": "⭐ Купить Premium",
        "btn_sale": "🔥 Акция месяца",
        "btn_change_lang": "🌐 Сменить язык",
    },

    "kg": {
        "choose_lang": "Тилди тандаңыз:",
        "menu": "Башкы меню:",
        "btn_analyze": "🔍 Товар анализи (демо)",
        "btn_trends": "📊 Тренддер (демо)",
        "btn_cabinet": "📂 Менин кабинетим",
        "btn_buy": "⭐ Премиум алуу",
        "btn_sale": "🔥 Айдын акциясы",
        "btn_change_lang": "🌐 Тилди өзгөртүү",
    },

    "kz": {
        "choose_lang": "Тілді таңдаңыз:",
        "menu": "Басты мәзір:",
        "btn_analyze": "🔍 Тауар талдауы (демо)",
        "btn_trends": "📊 Трендтер (демо)",
        "btn_cabinet": "📂 Жеке кабинет",
        "btn_buy": "⭐ Premium сатып алу",
        "btn_sale": "🔥 Ай акциясы",
        "btn_change_lang": "🌐 Тілді ауыстыру",
    },
}


def format_time(ts):
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ==========================
#        КЛАВИАТУРЫ
# ==========================
def keyboard_main(lang):
    t = LOCALES[lang]
    return ReplyKeyboardMarkup([
        [t["btn_analyze"]],
        [t["btn_trends"]],
        [t["btn_cabinet"]],
        [t["btn_buy"], t["btn_sale"]],
        [t["btn_change_lang"]],
    ], resize_keyboard=True)


def keyboard_lang():
    return ReplyKeyboardMarkup([
        ["🇰🇬 Кыргызча", "🇰🇿 Қазақша"],
        ["🇷🇺 Русский"],
    ], resize_keyboard=True)


# ==========================
#        ХЕНДЛЕРЫ
# ==========================
async def start(update: Update, context):
    user = update.effective_user
    register_user(user)

    # владелец
    if user.id == OWNER_ID:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET role='owner' WHERE user_id=?", (user.id,))
        conn.commit()
        conn.close()

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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        LOCALES[lang]["menu"],
        reply_markup=keyboard_main(lang)
    )


async def handle(update: Update, context):
    user = update.effective_user
    user_id = user.id

    increment_requests(user_id)

    data = get_user_data(user_id)
    lang = data["lang"]
    t = LOCALES[lang]
    text = update.message.text

    # ----- демо функционал -----
    if text == t["btn_analyze"]:
        await update.message.reply_text("🔍 Демо-анализ работает!")
        return

    if text == t["btn_trends"]:
        await update.message.reply_text("📊 Демо-тренды работают!")
        return

    # ----- личный кабинет -----
    if text == t["btn_cabinet"]:
        premium_status = (
            format_time(data["premium_until"])
            if data["premium_until"] and data["premium_until"] > time.time()
            else "Нет"
        )

        profile = f"""
📂 Личный кабинет

ID: {data['user_id']}
Username: @{data['username']}
Имя: {data['first_name']}
Роль: {data['role']}

Дата регистрации: {format_time(data['created_at'])}
Последний онлайн: {format_time(data['last_active'])}

Премиум до: {premium_status}
Всего запросов: {data['total_requests']}
"""
        await update.message.reply_text(profile, reply_markup=keyboard_main(lang))
        return

    # ----- акция месяца -----
    if text == t["btn_sale"]:
        await update.message.reply_text(f"""
🔥 АКЦИЯ МЕСЯЦА

1 месяц — 390 сом  
6 месяцев — 1690 сом  
12 месяцев — 2990 сом  

После оплаты отправьте чек: @{MANAGER_USERNAME}
        """)
        return

    # ----- покупка премиума -----
    if text == t["btn_buy"]:
        await update.message.reply_text(f"""
⭐ Premium возможности:

• Полный анализ товара  
• Подбор ниши  
• Проверка спроса  
• Анализ конкурентов  
• Идеи товаров  
• Тренды  
• Рекомендации по рекламе  
• Личный менеджер

💰 Цены:
1 месяц — 490 сом  
6 месяцев — 1990 сом  
12 месяцев — 3490 сом  

🔥 Сейчас действует акция! (Смотри кнопку Акция месяца)

После оплаты отправьте чек менеджеру: @{MANAGER_USERNAME}
        """)
        return

    # ----- смена языка -----
    if text == t["btn_change_lang"]:
        await update.message.reply_text(t["choose_lang"], reply_markup=keyboard_lang())
        return

    await update.message.reply_text("Команда пока не поддерживается.")


# ==========================
#   ADMIN: ДАТЬ ПРЕМИУМ
# ==========================
async def givepremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != OWNER_ID:
        await update.message.reply_text("Нет доступа.")
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
    except:
        await update.message.reply_text("Использование: /givepremium USER_ID DAYS")
        return

    until = set_premium(target_id, days)

    await update.message.reply_text(
        f"Премиум выдан!\nUser: {target_id}\nДней: {days}\nДо: {format_time(until)}"
    )


# ==========================
#             MAIN
# ==========================
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("givepremium", givepremium))
    app.add_handler(MessageHandler(filters.Regex("Кыргызча|Қазақша|Русский"), choose_lang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
