
import os
import time
import sqlite3
from typing import Optional

from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==========================
#          CONFIG
# ==========================

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

DB_PATH = "database.db"

# Владелец
OWNER_ID = 1974482384
OWNER_USERNAME = "ihaariss"

# Менеджер по умолчанию
DEFAULT_MANAGER_ID = 571499876
DEFAULT_MANAGER_USERNAME = "Artbazar_support"

# Порт и URL для webhook (Fly.io)
PORT = int(os.getenv("PORT", "8080"))
APP_URL = os.getenv("APP_URL")
if not APP_URL:
    app_name = os.getenv("FLY_APP_NAME", "artbazarbot")
    APP_URL = f"https://{app_name}.fly.dev"


# ==========================
#          БАЗА ДАННЫХ
# ==========================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',   -- user / manager / owner
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
        INSERT INTO users (user_id, username, first_name, created_at, last_active)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_active = excluded.last_active
        """,
        (user.id, user.username, user.first_name, now, now),
    )
    conn.commit()

    # Назначаем роли владельцу и базовому менеджеру
    if user.id == OWNER_ID:
        c.execute("UPDATE users SET role='owner' WHERE user_id=?", (user.id,))
    elif user.id == DEFAULT_MANAGER_ID:
        c.execute("UPDATE users SET role='manager' WHERE user_id=?", (user.id,))

    conn.commit()
    conn.close()


def get_user_data(user_id) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT user_id, username, first_name, role, lang,
               premium_until, created_at, last_active, total_requests
        FROM users WHERE user_id=?
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


def increment_requests(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        UPDATE users SET total_requests = total_requests + 1,
                         last_active = ?
        WHERE user_id=?
        """,
        (int(time.time()), user_id),
    )
    conn.commit()
    conn.close()


def set_role(user_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    conn.commit()
    conn.close()


def set_premium(user_id, days):
    premium_until = int(time.time()) + days * 24 * 3600
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET premium_until=? WHERE user_id=?",
        (premium_until, user_id),
    )
    conn.commit()
    conn.close()
    return premium_until


def get_stats():
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM users WHERE premium_until IS NOT NULL AND premium_until>?",
        (now,),
    )
    premium_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE role='manager'")
    managers = c.fetchone()[0]

    since_24h = now - 24 * 3600
    c.execute("SELECT COUNT(*) FROM users WHERE last_active>?", (since_24h,))
    active_24h = c.fetchone()[0]

    conn.close()

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "managers": managers,
        "active_24h": active_24h,
    }


# ==========================
#        ЛОКАЛИЗАЦИЯ
# ==========================

LOCALES = {
    "ru": {
        "choose_lang": "Выберите язык:",
        "menu": "Главное меню:",
        "btn_niche": "🔍 Подбор ниши",
        "btn_market": "📈 Анализ рынка",
        "btn_competitors": "🏁 Анализ конкурентов",
        "btn_trends": "📊 Тренды",
        "btn_ideas": "💡 Идеи товаров",
        "btn_margin": "🧮 Калькулятор маржи",
        "btn_ai": "🤖 AI-анализ (Premium)",
        "btn_cabinet": "📂 Мой кабинет",
        "btn_buy": "⭐ Купить Premium",
        "btn_sale": "🔥 Акция месяца",
        "btn_change_lang": "🌐 Сменить язык",
        # Менеджер
        "btn_manager_give": "⭐ Выдать премиум",
        "btn_manager_stats": "📊 Статистика (24 ч)",
        # Владелец
        "btn_owner_stats": "📊 Полная статистика",
        "btn_owner_managers": "👨‍💼 Менеджеры",
        "not_allowed": "У вас нет доступа к этой команде.",
        "ask_niche": (
            "Расскажи, какой у тебя опыт, стартовый бюджет, страна/город и где хочешь продавать "
            "(маркетплейс, Instagram, офлайн и т.п.).\n\n"
            "Напиши всё в одном сообщении — я подберу 3–7 ниш с плюсами и рисками."
        ),
        "ask_market": (
            "Опиши рынок, который тебя интересует.\n\n"
            "Формат: страна/город, категория товаров, формат продаж (маркетплейс, соцсети, офлайн), "
            "уровень цен (бюджет/средний/премиум)."
        ),
        "ask_competitors": (
            "Опиши своих основных конкурентов: что продают, по каким ценам, на каких площадках, "
            "в чём их сильные стороны (по твоему мнению).\n\n"
            "Можно просто дать список или кратко описать 3–5 игроков рынка."
        ),
        "ask_trends": (
            "Укажи страну/регион и категорию, по которой хочешь посмотреть тренды.\n\n"
            "Например: «Казахстан, товары для дома», или «Онлайн-образование для предпринимателей в СНГ».\n\n"
            "Важно: это не живые данные с маркетплейсов, а аналитика по общим трендам и логике рынка."
        ),
        "ask_ideas": (
            "Напиши, какой у тебя опыт, что тебе интересно, какой бюджет на старт и какой формат продаж "
            "рассматриваешь.\n\n"
            "На основе этого предложу 5–15 идей товаров/направлений."
        ),
        "ask_ai": "Введите товар или нишу для глубокого AI-анализа (Premium):",
        "no_premium": "⚠ Доступно только Premium. Нажмите: ⭐ Купить Premium",
        "manager_give_prompt": (
            "Отправь в одном сообщении: <code>USER_ID КОЛИЧЕСТВО_ДНЕЙ</code>\n"
            "Например: <code>123456789 30</code>"
        ),
    },
}


def format_time(ts):
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ==========================
#        КЛАВИАТУРЫ
# ==========================

def keyboard_user(lang: str = "ru"):
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_niche"], t["btn_market"]],
            [t["btn_competitors"], t["btn_trends"]],
            [t["btn_ideas"], t["btn_margin"]],
            [t["btn_cabinet"]],
            [t["btn_buy"], t["btn_sale"]],
            [t["btn_change_lang"]],
        ],
        resize_keyboard=True,
    )


def keyboard_lang():
    return ReplyKeyboardMarkup(
        [["🇰🇬 Кыргызча", "🇰🇿 Қазақша"], ["🇷🇺 Русский"]],
        resize_keyboard=True,
    )


def keyboard_manager():
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_manager_give"], t["btn_manager_stats"]],
            [t["btn_cabinet"]],
            [t["btn_change_lang"]],
        ],
        resize_keyboard=True,
    )


def keyboard_owner():
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_owner_stats"], t["btn_owner_managers"]],
            [t["btn_manager_give"]],
            [t["btn_cabinet"]],
            [t["btn_change_lang"]],
        ],
        resize_keyboard=True,
    )


# ==========================
#      AI-ПОМОЩНИКИ
# ==========================

def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    if client is None:
        return "⚠ OpenAI ключ не настроен. Обратись к владельцу бота."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def ai_niche(query: str) -> str:
    system = (
        "Ты бизнес-аналитик и продуктолог. Помогаешь предпринимателям подбирать ниши под их опыт, бюджет и рынок."
        " Отвечай структурно, по делу, без воды."
    )
    user = (
        "Данные о запросе на подбор ниши:\n"
        f"{query}\n\n"
        "Сформируй ответ:\n"
        "1) Краткий профиль предпринимателя.\n"
        "2) 3–7 конкретных ниш (название + формат продаж).\n"
        "3) Для каждой ниши: плюсы, риски, пример цен/чека, пример воронки продаж.\n"
        "4) Какую нишу рекомендовать на старт и почему.\n"
    )
    return _call_openai(system, user)


def ai_market(query: str) -> str:
    system = (
        "Ты эксперт по анализу рынков в СНГ. Учитываешь платёжеспособность, конкуренцию, формат продаж и т.д."
    )
    user = (
        "Исходные данные для анализа рынка:\n"
        f"{query}\n\n"
        "Сделай:\n"
        "1) Обзор рынка.\n"
        "2) Портрет клиента.\n"
        "3) Оценка конкуренции.\n"
        "4) Риски и барьеры входа.\n"
        "5) Практические рекомендации по заходу на рынок.\n"
    )
    return _call_openai(system, user)


def ai_competitors(query: str) -> str:
    system = (
        "Ты специалист по конкурентному анализу. Разбираешь сильные и слабые стороны конкурентов "
        "и предлагаешь стратегию дифференциации."
    )
    user = (
        "Описание конкурентов:\n"
        f"{query}\n\n"
        "Дай анализ:\n"
        "1) Кто конкуренты и что предлагают.\n"
        "2) Их сильные стороны.\n"
        "3) Слабые места.\n"
        "4) Точки дифференциации для нашего проекта.\n"
        "5) Рекомендации по позиционированию.\n"
    )
    return _call_openai(system, user)


def ai_trends(query: str) -> str:
    system = (
        "Ты аналитик по трендам в e-commerce. Указывай, что это стратегический взгляд, "
        "а не точные данные с маркетплейсов."
    )
    user = (
        "Запрос по трендам:\n"
        f"{query}\n\n"
        "Нужно:\n"
        "1) 5–10 актуальных трендов в этой категории/регионе.\n"
        "2) Почему они появились.\n"
        "3) Какие товары/форматы подходят под эти тренды.\n"
        "4) Какие тренды перегреты, где есть окно возможностей.\n"
    )
    return _call_openai(system, user)


def ai_ideas(query: str) -> str:
    system = (
        "Ты продакт-менеджер и предприниматель. Генерируешь идеи товаров/направлений под конкретного человека."
    )
    user = (
        "Данные о человеке и его запросе на идеи:\n"
        f"{query}\n\n"
        "Сделай:\n"
        "1) Краткий портрет.\n"
        "2) 5–15 идей с описанием.\n"
        "3) Формат продаж, пример чека, плюс/минус по сложности для каждой идеи.\n"
        "4) 1–2 лучших варианта на старт и почему.\n"
    )
    return _call_openai(system, user)


def ai_premium_analyze(query: str) -> str:
    system = (
        "Ты senior-аналитик по товарному бизнесу и маркетплейсам. Делаешь глубокий разбор товара или ниши."
    )
    user = (
        "Объект для анализа (товар или ниша):\n"
        f"{query}\n\n"
        "Нужно:\n"
        "1) Резюме — стоит ли лезть.\n"
        "2) Спрос и ЦА.\n"
        "3) Конкуренция и позиционирование.\n"
        "4) Пример математики.\n"
        "5) Риски.\n"
        "6) Пошаговый план теста на 2–4 недели.\n"
    )
    return _call_openai(system, user, max_tokens=800)


# ==========================
#      КАЛЬКУЛЯТОР МАРЖИ
# ==========================

def _parse_number(text: str):
    text = text.replace(" ", "").replace(",", ".")
    return float(text)


def build_margin_response(cost, price, extra):
    cost = float(cost)
    price = float(price)
    extra = float(extra)

    prime_cost = cost + extra
    profit = price - prime_cost
    margin_percent = (profit / price * 100) if price > 0 else 0
    roi = (profit / cost * 100) if cost > 0 else 0

    def fmt(x):
        return (
            str(round(x, 2)).rstrip("0").rstrip(".")
            if isinstance(x, float)
            else str(x)
        )

    if profit <= 0:
        verdict = "🔴 Маржа отрицательная или нулевая — в таком виде товар невыгоден."
    elif margin_percent >= 30 and roi >= 50:
        verdict = "🟢 Хорошая маржа, товар перспективный."
    elif margin_percent < 15:
        verdict = "🟠 Маржа слабая. Нужна более высокая цена или более дешёвая закупка."
    else:
        verdict = "🟡 Средняя маржа, можно тестировать, но смотри по конкуренции."

    text = f"""
📊 <b>Расчёт маржи</b>

💰 Закупка: <b>{fmt(cost)}</b> сом  
🧾 Затраты (доставка, упаковка, комиссии): <b>{fmt(extra)}</b> сом  
🛒 Цена продажи: <b>{fmt(price)}</b> сом  

— — —

🔥 Чистая прибыль: <b>{fmt(profit)}</b> сом  
💹 Маржинальность: <b>{fmt(margin_percent)}%</b>  
🚀 ROI: <b>{fmt(roi)}%</b>  
📦 Себестоимость: <b>{fmt(prime_cost)}</b> сом  

— — —

{verdict}
""".strip()

    return text


# ==========================
#          ХЕНДЛЕРЫ
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)

    data = get_user_data(user.id)

    if data["role"] == "owner":
        await update.message.reply_text(
            "Ты владелец бота. Клиентское меню — ниже. Для админ-панели используй команду /admin.",
            reply_markup=keyboard_user(),
        )
    elif data["role"] == "manager":
        await update.message.reply_text(
            "Вы менеджер. Для работы с премиумом используйте /admin.",
            reply_markup=keyboard_user(),
        )
    else:
        await update.message.reply_text(
            LOCALES["ru"]["choose_lang"],
            reply_markup=keyboard_lang(),
        )


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        LOCALES["ru"]["menu"], reply_markup=keyboard_user()
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user_data(user.id)

    if not data or data["role"] not in ("owner", "manager"):
        await update.message.reply_text(LOCALES["ru"]["not_allowed"])
        return

    if data["role"] == "owner":
        await update.message.reply_text(
            "👑 Админ-панель владельца", reply_markup=keyboard_owner()
        )
    else:
        await update.message.reply_text(
            "👨‍💼 Менеджер-меню", reply_markup=keyboard_manager()
        )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text or ""
    t = LOCALES["ru"]

    data = get_user_data(user_id)
    if not data:
        register_user(user)
        data = get_user_data(user_id)

    increment_requests(user_id)

    role = data["role"]
    mode = context.user_data.get("mode")

    # ====== режим выдачи премиума менеджером/владельцем ======
    if mode == "manager_givepremium" and role in ("manager", "owner"):
        context.user_data["mode"] = None
        try:
            parts = text.strip().split()
            target_id = int(parts[0])
            days = int(parts[1])
        except Exception:
            await update.message.reply_text(
                "Неверный формат. Пример: <code>123456789 30</code>",
                parse_mode="HTML",
            )
            return

        until = set_premium(target_id, days)
        await update.message.reply_text(
            f"Премиум выдан пользователю {target_id} на {days} дней.\nДо: {format_time(until)}"
        )
        return

    # ====== режим калькулятора маржи ======
    if mode == "margin":
        step = context.user_data.get("margin_step")

        if step == "cost":
            try:
                cost = _parse_number(text)
                if cost <= 0:
                    raise ValueError
            except Exception:
                await update.message.reply_text(
                    "Пожалуйста, укажи закупочную цену цифрами, например: 800"
                )
                return

            context.user_data["margin_cost"] = cost
            context.user_data["margin_step"] = "price"
            await update.message.reply_text(
                "Теперь введи цену продажи.\nНапример: 1500"
            )
            return

        if step == "price":
            try:
                price = _parse_number(text)
                if price <= 0:
                    raise ValueError
            except Exception:
                await update.message.reply_text(
                    "Пожалуйста, укажи цену продажи цифрами, например: 1500"
                )
                return

            context.user_data["margin_price"] = price
            context.user_data["margin_step"] = "extra"
            await update.message.reply_text(
                "Укажи дополнительные расходы (доставка, упаковка, комиссии).\n"
                "Если хочешь пропустить — напиши 0."
            )
            return

        if step == "extra":
            try:
                extra = _parse_number(text)
                if extra < 0:
                    raise ValueError
            except Exception:
                await update.message.reply_text(
                    "Пожалуйста, укажи расходы цифрами, например: 200 или 0."
                )
                return

            cost = context.user_data.get("margin_cost", 0)
            price = context.user_data.get("margin_price", 0)

            context.user_data["mode"] = None
            context.user_data["margin_step"] = None
            context.user_data.pop("margin_cost", None)
            context.user_data.pop("margin_price", None)

            result_text = build_margin_response(cost, price, extra)
            await update.message.reply_text(result_text, parse_mode="HTML")
            return

    # ====== AI режимы ======
    if mode == "niche":
        context.user_data["mode"] = None
        try:
            result = ai_niche(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text(
                "Не удалось проанализировать нишу. Проверь OpenAI-ключ."
            )
        return

    if mode == "market":
        context.user_data["mode"] = None
        try:
            result = ai_market(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка при анализе рынка.")
        return

    if mode == "competitors":
        context.user_data["mode"] = None
        try:
            result = ai_competitors(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text(
                "Ошибка при анализе конкурентов."
            )
        return

    if mode == "trends":
        context.user_data["mode"] = None
        try:
            result = ai_trends(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text(
                "Не удалось получить трендовую аналитику."
            )
        return

    if mode == "ideas":
        context.user_data["mode"] = None
        try:
            result = ai_ideas(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text(
                "Ошибка при генерации идей."
            )
        return

    if mode == "ai_premium":
        context.user_data["mode"] = None
        try:
            result = ai_premium_analyze(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка AI-анализа.")
        return

    # ====== КНОПКИ ПОЛЬЗОВАТЕЛЯ ======
    if text == t["btn_niche"]:
        context.user_data["mode"] = "niche"
        await update.message.reply_text(t["ask_niche"])
        return

    if text == t["btn_market"]:
        context.user_data["mode"] = "market"
        await update.message.reply_text(t["ask_market"])
        return

    if text == t["btn_competitors"]:
        context.user_data["mode"] = "competitors"
        await update.message.reply_text(t["ask_competitors"])
        return

    if text == t["btn_trends"]:
        context.user_data["mode"] = "trends"
        await update.message.reply_text(t["ask_trends"])
        return

    if text == t["btn_ideas"]:
        context.user_data["mode"] = "ideas"
        await update.message.reply_text(t["ask_ideas"])
        return

    if text == t["btn_margin"]:
        context.user_data["mode"] = "margin"
        context.user_data["margin_step"] = "cost"
        await update.message.reply_text(
            "Введи закупочную цену товара в сомах.\nНапример: 800"
        )
        return

    if text == t["btn_ai"]:
        if not data["premium_until"] or data["premium_until"] < time.time():
            await update.message.reply_text(t["no_premium"])
            return
        context.user_data["mode"] = "ai_premium"
        await update.message.reply_text(t["ask_ai"])
        return

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
        await update.message.reply_text(
            profile, reply_markup=keyboard_user()
        )
        return

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

После оплаты отправьте чек менеджеру: @{DEFAULT_MANAGER_USERNAME}
""".strip()
        )
        return

    if text == t["btn_sale"]:
        await update.message.reply_text(
            f"""
🔥 АКЦИЯ:

1 месяц — 390 сом  
6 месяцев — 1690 сом  
1 год — 2990 сом  

Отправь чек менеджеру: @{DEFAULT_MANAGER_USERNAME}
""".strip()
        )
        return

    if text == t["btn_change_lang"]:
        await update.message.reply_text(
            LOCALES["ru"]["choose_lang"],
            reply_markup=keyboard_lang(),
        )
        return

    # ====== КНОПКИ МЕНЕДЖЕРА / ВЛАДЕЛЬЦА ======
    if text == t["btn_manager_give"] and role in ("manager", "owner"):
        context.user_data["mode"] = "manager_givepremium"
        await update.message.reply_text(
            t["manager_give_prompt"], parse_mode="HTML"
        )
        return

    if text == t["btn_manager_stats"] and role in ("manager", "owner"):
        s = get_stats()
        msg = f"""
📊 Статистика за сутки:

Всего пользователей: {s['total_users']}
Премиум-пользователей: {s['premium_users']}
Менеджеров: {s['managers']}
Активно за 24 ч: {s['active_24h']}
"""
        await update.message.reply_text(msg)
        return

    if text == LOCALES["ru"]["btn_owner_stats"] and role == "owner":
        s = get_stats()
        msg = f"""
👑 Полная статистика:

Всего пользователей: {s['total_users']}
Премиум-пользователей: {s['premium_users']}
Менеджеров: {s['managers']}
Активно за 24 ч: {s['active_24h']}
"""
        await update.message.reply_text(msg)
        return

    await update.message.reply_text(
        "Команда пока не поддерживается. Нажми кнопку в меню."
    )


# ==========================
#      ADMIN COMMANDS
# ==========================

async def addmanager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.message.reply_text(LOCALES["ru"]["not_allowed"])
        return

    if not context.args:
        await update.message.reply_text("Использование: /addmanager @username")
        return

    username = context.args[0].lstrip("@")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text(
            "Этот пользователь ещё не запускал бота. Пусть сначала нажмёт /start."
        )
        return

    set_role(row[0], "manager")
    await update.message.reply_text(
        f"Пользователь @{username} назначен менеджером."
    )


async def removemanager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.message.reply_text(LOCALES["ru"]["not_allowed"])
        return

    if not context.args:
        await update.message.reply_text("Использование: /removemanager @username")
        return

    username = context.args[0].lstrip("@")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("Пользователь не найден в БД.")
        return

    set_role(row[0], "user")
    await update.message.reply_text(
        f"Пользователь @{username} снят с роли менеджера."
    )


async def givepremium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user_data(user.id)

    if not data or data["role"] not in ("owner", "manager"):
        await update.message.reply_text(LOCALES["ru"]["not_allowed"])
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
    except Exception:
        await update.message.reply_text(
            "Использование: /givepremium USER_ID DAYS"
        )
        return

    until = set_premium(target_id, days)
    await update.message.reply_text(
        f"Премиум выдан пользователю {target_id} на {days} дней.\nДо: {format_time(until)}"
    )


# ==========================
#             MAIN
# ==========================

def main():
    init_db()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("addmanager", addmanager))
    application.add_handler(CommandHandler("removemanager", removemanager))
    application.add_handler(CommandHandler("givepremium", givepremium_cmd))

    application.add_handler(
        MessageHandler(
            filters.Regex("Кыргызча|Қазақша|Русский"), choose_lang
        )
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle)
    )

    # Webhook-режим под Fly.io
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{APP_URL}/{TOKEN}",
    )


if __name__ == "__main__":
    main()
