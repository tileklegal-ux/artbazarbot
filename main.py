import os
import time
import sqlite3
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------------------------
#   КОНФИГ
# ------------------------
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = "database.db"

# Владелец (ты)
OWNER_ID = 1974482384   # @ihaariss

# Менеджер (поддержка)
MANAGER_USERNAME = "Artha3ar_support"
MANAGER_ID = 571499876  # @Artha3ar_support

client = OpenAI(api_key=OPENAI_KEY)


# ------------------------
#   БАЗА ДАННЫХ
# ------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()


def register_user(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = int(time.time())
    c.execute(
        """
        INSERT INTO users (user_id, username, first_name, role, created_at, last_active)
        VALUES (?, ?, ?, 'user', ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_active = excluded.last_active
        """,
        (user.id, user.username, user.first_name, now, now),
    )
    conn.commit()
    conn.close()


def get_user_data(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT user_id, username, first_name, role, lang,
               premium_until, created_at, last_active, total_requests
        FROM users WHERE user_id = ?
        """,
        (user_id,),
    )
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


def set_role(user_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
    conn.commit()
    conn.close()


def increment_requests(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()


def set_premium(user_id: int, days: int):
    premium_until = int(time.time()) + days * 24 * 3600
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET premium_until = ? WHERE user_id = ?",
        (premium_until, user_id),
    )
    conn.commit()
    conn.close()
    return premium_until


# ------------------------
#   ЛОКАЛИЗАЦИЯ
# ------------------------
LOCALES = {
    "ru": {
        "choose_lang": "Выберите язык:",
        "menu_user": "Главное меню:",
        "menu_owner": "Меню владельца:",
        "menu_manager": "Меню менеджера:",

        # Кнопки для пользователей
        "btn_analyze": "🔍 Анализ товара (демо)",
        "btn_ai": "🤖 AI-анализ (Premium)",
        "btn_trends": "📊 Тренды (демо)",
        "btn_cabinet": "📂 Мой кабинет",
        "btn_buy": "⭐ Купить Premium",
        "btn_sale": "🔥 Акция месяца",
        "btn_change_lang": "🌐 Сменить язык",

        # Кнопки для владельца
        "btn_owner_panel": "👑 Панель владельца",
        "btn_owner_users": "👤 Пользователи",
        "btn_owner_premium": "⭐ Выдать премиум",
        "btn_owner_stats": "📊 Статистика",
        "btn_owner_broadcast": "📣 Рассылка",

        # Кнопки для менеджера
        "btn_manager_panel": "🛠 Панель менеджера",
        "btn_manager_pending": "📋 Ожидают оплаты",
        "btn_manager_approve": "✅ Подтвердить премиум",

        # Общие
        "btn_back_user": "⬅️ В меню пользователя",

        "ask_ai": "Введите товар или нишу для AI-анализа:",
        "no_premium": "⚠ Доступно только Premium. Нажмите: ⭐ Купить Premium",
        "not_allowed": "Нет доступа.",
        "unknown_cmd": "Команда пока не поддерживается.",
    },
}


def format_time(ts: int | None) -> str:
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ------------------------
#   КЛАВИАТУРЫ
# ------------------------
def keyboard_user(lang: str = "ru") -> ReplyKeyboardMarkup:
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_analyze"], t["btn_ai"]],
            [t["btn_trends"]],
            [t["btn_cabinet"]],
            [t["btn_buy"], t["btn_sale"]],
            [t["btn_change_lang"]],
        ],
        resize_keyboard=True,
    )


def keyboard_owner(lang: str = "ru") -> ReplyKeyboardMarkup:
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_analyze"], t["btn_ai"]],
            [t["btn_trends"]],
            [t["btn_owner_users"], t["btn_owner_premium"]],
            [t["btn_owner_stats"], t["btn_owner_broadcast"]],
            [t["btn_cabinet"], t["btn_back_user"]],
        ],
        resize_keyboard=True,
    )


def keyboard_manager(lang: str = "ru") -> ReplyKeyboardMarkup:
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_cabinet"]],
            [t["btn_manager_pending"], t["btn_manager_approve"]],
            [t["btn_back_user"]],
        ],
        resize_keyboard=True,
    )


def keyboard_lang() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["🇰🇬 Кыргызча", "🇰🇿 Қазақша"],
            ["🇷🇺 Русский"],
        ],
        resize_keyboard=True,
    )


# ------------------------
#   AI АНАЛИЗ
# ------------------------
def ai_analyze(query: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Ты — эксперт по товарке, маркетплейсам и нишам.",
            },
            {
                "role": "user",
                "content": f"Анализ товара/ниши: {query}. Дай кратко: спрос, конкуренция, рекомендации.",
            },
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content


# ------------------------
#   ХЕНДЛЕРЫ
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)

    # проставляем роль владельца и менеджера по ID
    if user.id == OWNER_ID:
        set_role(user.id, "owner")
    elif user.id == MANAGER_ID:
        set_role(user.id, "manager")

    await update.message.reply_text(
        LOCALES["ru"]["choose_lang"], reply_markup=keyboard_lang()
    )


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user_data(user.id)
    role = data["role"] if data else "user"
    t = LOCALES["ru"]

    if role == "owner":
        await update.message.reply_text(
            t["menu_owner"], reply_markup=keyboard_owner()
        )
    elif role == "manager":
        await update.message.reply_text(
            t["menu_manager"], reply_markup=keyboard_manager()
        )
    else:
        await update.message.reply_text(
            t["menu_user"], reply_markup=keyboard_user()
        )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user_data(user.id)

    # если по какой-то причине нет записи - регистрируем
    if not data:
        register_user(user)
        data = get_user_data(user.id)

    role = data["role"]
    text = update.message.text
    t = LOCALES["ru"]

    increment_requests(user.id)

    if role == "owner":
        await handle_owner(update, context, data, text, t)
    elif role == "manager":
        await handle_manager(update, context, data, text, t)
    else:
        await handle_user(update, context, data, text, t)


# ------------------------
#   ЛОГИКА ПОЛЬЗОВАТЕЛЯ
# ------------------------
async def handle_user(update, context, data, text, t):
    user_id = data["user_id"]

    # Аналитика (демо)
    if text == t["btn_analyze"]:
        await update.message.reply_text("🔍 Демо-анализ работает!")
        return

    # AI анализ (premium)
    if text == t["btn_ai"]:
        if not data["premium_until"] or data["premium_until"] < time.time():
            await update.message.reply_text(t["no_premium"])
            return
        context.user_data["mode"] = "ai"
        await update.message.reply_text(t["ask_ai"])
        return

    # ответ AI по товару/нише
    if context.user_data.get("mode") == "ai":
        context.user_data["mode"] = None
        try:
            result = ai_analyze(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка AI. Проверь ключ.")
        return

    # тренды (демо)
    if text == t["btn_trends"]:
        await update.message.reply_text("📊 Демо-тренды работают!")
        return

    # личный кабинет
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
        await update.message.reply_text(profile, reply_markup=keyboard_user())
        return

    # покупка премиума
    if text == t["btn_buy"]:
        await update.message.reply_text(
            f"""
⭐ ТАРИФЫ PREMIUM:

1 месяц — 490 сом  
6 месяцев — 1990 сом  
1 год — 3490 сом  

🔥 АКЦИЯ (до конца месяца):

1 месяц — 390 сом  
6 месяцев — 1690 сом  
1 год — 2990 сом  

После оплаты отправьте чек менеджеру: @{MANAGER_USERNAME}
"""
        )
        return

    # акция
    if text == t["btn_sale"]:
        await update.message.reply_text(
            f"""
🔥 АКЦИЯ:

1 месяц — 390 сом  
6 месяцев — 1690 сом  
1 год — 2990 сом  

Отправьте чек менеджеру: @{MANAGER_USERNAME}
"""
        )
        return

    # смена языка (пока просто заново меню)
    if text == t["btn_change_lang"]:
        await update.message.reply_text(
            t["choose_lang"], reply_markup=keyboard_lang()
        )
        return

    await update.message.reply_text(t["unknown_cmd"], reply_markup=keyboard_user())


# ------------------------
#   ЛОГИКА ВЛАДЕЛЬЦА
# ------------------------
async def handle_owner(update, context, data, text, t):
    # переход в обычное меню пользователя
    if text == t["btn_back_user"]:
        await update.message.reply_text(
            t["menu_user"], reply_markup=keyboard_user()
        )
        return

    # панель, пользователи, премиум и т.д.
    if text == t["btn_owner_users"]:
        await update.message.reply_text(
            "👤 Раздел пользователей в разработке.\nБудет список, фильтры, поиск по ID/username."
        )
        return

    if text == t["btn_owner_premium"]:
        await update.message.reply_text(
            "⭐ Премиум-выдача пока через команду:\n\n/givepremium USER_ID DAYS"
        )
        return

    if text == t["btn_owner_stats"]:
        await update.message.reply_text(
            "📊 Статистика в разработке.\nПокажем: активных пользователей, премиумов, запросов."
        )
        return

    if text == t["btn_owner_broadcast"]:
        await update.message.reply_text(
            "📣 Массовая рассылка появится позже.\nПока можно делать это вручную или через отдельный скрипт."
        )
        return

    # владелец тоже может пользоваться функциями пользователя
    await handle_user(update, context, data, text, t)


# ------------------------
#   ЛОГИКА МЕНЕДЖЕРА
# ------------------------
async def handle_manager(update, context, data, text, t):
    # менеджер может переключиться в пользовательское меню
    if text == t["btn_back_user"]:
        await update.message.reply_text(
            t["menu_user"], reply_markup=keyboard_user()
        )
        return

    if text == t["btn_cabinet"]:
        premium_status = (
            format_time(data["premium_until"])
            if data["premium_until"] and data["premium_until"] > time.time()
            else "Нет"
        )
        profile = f"""
📂 Кабинет менеджера

ID: {data['user_id']}
Username: @{data['username']}
Имя: {data['first_name']}
Роль: {data['role']}

Премиум до: {premium_status}
Всего запросов: {data['total_requests']}
"""
        await update.message.reply_text(profile, reply_markup=keyboard_manager())
        return

    if text == t["btn_manager_pending"]:
        await update.message.reply_text(
            "📋 Модуль 'ожидают оплаты' пока в разработке.\nПозже здесь будут заявки с чеков."
        )
        return

    if text == t["btn_manager_approve"]:
        await update.message.reply_text(
            "✅ Подтверждение премиума пока через владельца.\nПозже дадим менеджеру отдельную команду /approve."
        )
        return

    await update.message.reply_text(
        t["unknown_cmd"], reply_markup=keyboard_manager()
    )


# ------------------------
#   АДМИН-КОМАНДЫ
# ------------------------
async def givepremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    t = LOCALES["ru"]

    if user_id != OWNER_ID:
        await update.message.reply_text(t["not_allowed"])
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
    except Exception:
        await update.message.reply_text("Использование: /givepremium USER_ID DAYS")
        return

    until = set_premium(target_id, days)
    await update.message.reply_text(
        f"Премиум выдан пользователю {target_id} на {days} дней.\nДо: {format_time(until)}"
    )


async def setrole_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    t = LOCALES["ru"]

    if user_id != OWNER_ID:
        await update.message.reply_text(t["not_allowed"])
        return

    try:
        target_id = int(context.args[0])
        role = context.args[1]
    except Exception:
        await update.message.reply_text(
            "Использование: /setrole USER_ID role\nПример: /setrole 571499876 manager"
        )
        return

    if role not in ("user", "manager", "owner"):
        await update.message.reply_text("Роль должна быть: user / manager / owner")
        return

    set_role(target_id, role)
    await update.message.reply_text(
        f"Роль пользователя {target_id} изменена на: {role}"
    )


# ------------------------
#   MAIN
# ------------------------
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("givepremium", givepremium))
    app.add_handler(CommandHandler("setrole", setrole_cmd))

    app.add_handler(
        MessageHandler(
            filters.Regex("Кыргызча|Қазақша|Русский"), choose_lang
        )
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
