import os
import time
import sqlite3
from typing import Optional

from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==========================
#      НАСТРОЙКИ
# ==========================

TOKEN = os.getenv("BOT_TOKEN")  # ЧИТАЕМ ИЗ FLY.IO SECRETS
APP_URL = os.getenv("APP_URL")  # URL вебхука

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DB_PATH = "artbazarbot.db"

# РОЛИ
OWNER_ID = 1974482384        # Тилек
DEFAULT_MANAGER_ID = 571499876
DEFAULT_MANAGER_USERNAME = "Artbazar_support"

PREMIUM_ONE_MONTH = 30 * 24 * 60 * 60

PORT = int(os.getenv("PORT", "8080"))

# ==========================
#      БАЗА ДАННЫХ
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
            role TEXT DEFAULT 'user',
            premium_until INTEGER DEFAULT 0,
            created_at INTEGER,
            last_active INTEGER,
            request_count INTEGER DEFAULT 0
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            manager_id INTEGER,
            months INTEGER,
            created_at INTEGER
        )
        """
        )

    conn.commit()
    conn.close()

def get_user_data(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT user_id, username, first_name, role, premium_until,
               created_at, last_active, recommended
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
        "premium_until": row[4],
        "created_at": row[5],
        "last_active": row[6],
        "request_count": row[7],
    }


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
    conn.close()


def increment_requests(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = int(time.time())

    c.execute(
        """
        UPDATE users
        SET request_count = COALESCE(request_count,0) + 1,
            last_active = ?
        WHERE user_id = ?
        """,
        (now, user_id),
    )

    conn.commit()
    conn.close()


def set_role(user_id: int, role: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))

    conn.commit()
    conn.close()


def give_premium(user_id: int, months: int, manager_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())
    delta = months * PREMIUM_ONE_MONTH

    c.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    current_until = row[0] if row else 0

    # Если премиум истёк — начинаем с сегодняшнего дня
    if current_until < now:
        new_until = now + delta
    else:
        new_until = current_until + delta

    c.execute(
        "UPDATE users SET premium_until = ? WHERE user_id = ?",
        (new_until, user_id),
    )

    c.execute(
        """
        INSERT INTO premium_logs (user_id, manager_id, months, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, manager_id, months, now),
    )

    conn.commit()
    conn.close()
    return new_until


def get_stats_24h():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = int(time.time())
    day_ago = now - 24*60*60

    c.execute(
        "SELECT COUNT(*) FROM users WHERE created_at >= ?",
        (day_ago,),
    )
    new_users = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM users WHERE last_active >= ?",
        (day_ago,),
    )
    active_users = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM premium_logs WHERE created_at >= ?",
        (day_ago,),
    )
    new_premiums = c.fetchone()[0]

    conn.close()
    return new_users, active_users, new_premiums


def get_full_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    all_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE premium_until > ?", (time.time(),))
    active_premium = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM premium_logs")
    total_premium_events = c.fetchone()[0]

    conn.close()
    return all_users, active_premium, total_premium_events
    # ==========================
#      ТЕКСТЫ / ЛОКАЛИ
# ==========================

LOCALES = {
    "ru": {
        "menu": "Главное меню:",
        "choose_lang": "Выберите язык интерфейса:",
        "btn_niche": "🔍 Подбор ниши",
        "btn_market": "📈 Анализ рынка",
        "btn_competitors": "🏁 Анализ конкурентов",
        "btn_trends": "📊 Тренды",
        "btn_ideas": "💡 Идеи товаров",
        "btn_margin": "🧮 Калькулятор маржи",
        "btn_ai": "🤖 AI-анализ (Premium)",
        "btn_cabinet": "📂 Мой кабинет",
        "btn_buy": "⭐ Купить Premium",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_manager_give": "⭐ Выдать премиум",
        "btn_manager_stats": "📊 Статистика (24 ч)",
        "btn_owner_stats": "📊 Полная статистика",
        "btn_owner_managers": "👨‍💼 Менеджеры",
        "not_allowed": "У вас нет доступа к этой команде.",
        "ask_niche": (
            "Расскажи о себе: опыт, стартовый бюджет, страна и канал продаж.\n"
            "Например: «Одежда, бюджет 50к, Казахстан, продаю через Instagram»."
        ),
        "ask_market": (
            "Опиши рынок, который нужно проанализировать.\n"
            "Например: «товары для животных в Кыргызстане»."
        ),
        "ask_competitors": (
            "Отправь ссылки на конкурентов или их описания. Я разберу сильные и слабые стороны."
        ),
        "ask_trends": (
            "Укажи направление, страну/регион и формат продаж. Я дам анализ трендов."
        ),
        "ask_ideas": (
            "Расскажи о себе: опыт, интересы, формат продаж. Подберу идеи товаров для тебя."
        ),
        "ask_margin": (
            "Отправь данные в формате:\n"
            "Закуп 350\nДоставка 70\nКомиссия 15%\nЦена 1200\n"
        ),
        "ask_ai": (
            "Опиши товар или нишу, которую нужно разложить по полочкам. (Premium-режим)"
        ),
        "no_premium": (
            "Этот режим доступен только для Premium.\n"
            "Оформи подписку через «⭐ Купить Premium»."
        ),
        "cabinet_template": (
            "<b>Твой кабинет:</b>\n\n"
            "ID: {user_id}\n"
            "Роль: {role}\n"
            "Premium до: {premium_until}\n"
            "Запросов: {requests}\n"
        ),
        "premium_active_until": "Премиум активен до: {dt}",
        "premium_not_active": "Премиум ещё не подключён.",
    }
}


# ==========================
#      КЛАВИАТУРЫ
# ==========================

def keyboard_user(lang: str = "ru"):
    t = LOCALES["ru"]
    return ReplyKeyboardMarkup(
        [
            [t["btn_niche"], t["btn_market"]],
            [t["btn_competitors"], t["btn_trends"]],
            [t["btn_ideas"], t["btn_margin"]],
            [t["btn_cabinet"]],
            [t["btn_buy"]],
            [t["btn_change_lang"]],
        ],
        resize_keyboard=True,
    )


def keyboard_lang():
    return ReplyKeyboardMarkup(
        [["🇰🇬 Кыргызча", "🇰🇿 Қазақша"], ["🇷🇺 Русский"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def keyboard_manager_owner(role: str):
    t = LOCALES["ru"]
    rows = []

    if role in ("manager", "owner"):
        rows.append([t["btn_manager_give"], t["btn_manager_stats"]])

    if role == "owner":
        rows.append([t["btn_owner_stats"], t["btn_owner_managers"]])

    if rows:
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)

    return None
    # ==========================
#      AI — ПОМОЩНИКИ
# ==========================

def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """Обёртка для обращения к OpenAI."""
    if client is None:
        return "⚠ OpenAI API ключ не найден. Обратись к владельцу бота."

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
    )

    return resp.choices[0].message.content


# --------------------------
#        ПОДБОР НИШИ
# --------------------------

def ai_niche(query: str, premium: bool) -> str:
    system_prompt = (
        "Ты бизнес-аналитик и продуктолог. "
        "Отвечай структурно, по делу, не используй длинных простыней."
    )

    if premium:
        user_prompt = f"""
Запрос для полного премиального анализа ниши:

{query}

Нужно дать полный отчёт:
1) Краткий профиль предпринимателя.
2) 5–7 ниш (название + формат продаж).
3) Для каждой ниши: плюсы, риски, пример чека.
4) Пример юнит-экономики на 1–2 нишах.
5) Какую нишу рекомендовать и почему.
6) План действий на 2–4 недели.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)

    else:
        user_prompt = f"""
Запрос на демо-анализ ниши:

{query}

Сделай короткий ответ:
1) Тип предпринимателя — 1–2 предложения.
2) 2–3 ниши.
3) К каждой по 1 плюсу и 1 риску.
4) Что логично протестировать сначала.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=350)


# --------------------------
#        АНАЛИЗ РЫНКА
# --------------------------

def ai_market(query: str, premium: bool) -> str:
    system_prompt = (
        "Ты эксперт по анализу рынков в СНГ. "
        "Учитывай локальный спрос, конкуренцию и потребительское поведение."
    )

    if premium:
        user_prompt = f"""
Полный анализ рынка:

{query}

Сформируй отчёт:
1) Ёмкость рынка (качественно, без выдумывания цифр).
2) Сегменты аудитории.
3) Уровень конкуренции.
4) Барьеры входа.
5) Риски.
6) Рекомендации.
7) План теста на 2–4 недели.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)

    else:
        user_prompt = f"""
Краткий анализ рынка (демо):

{query}

Сделай коротко:
1) Что происходит на рынке (2–3 предложения).
2) Кто клиент.
3) Уровень конкуренции.
4) Главный плюс и главный риск.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=350)


# --------------------------
#     АНАЛИЗ КОНКУРЕНТОВ
# --------------------------

def ai_competitors(query: str, premium: bool) -> str:
    system_prompt = (
        "Ты эксперт по конкурентному анализу. "
        "Помогаешь понять сильные/слабые стороны рынка."
    )

    if premium:
        user_prompt = f"""
Полный анализ конкурентов:

{query}

1) Кто конкуренты и что продают.
2) Сильные стороны.
3) Слабые стороны.
4) Как выделиться.
5) Позиционирование.
6) Ошибки, которых избегать.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)

    else:
        user_prompt = f"""
Демо-анализ конкурентов:

{query}

Сделай коротко:
1) 2–3 предложения о конкуренции.
2) Один плюс рынка и один минус.
3) Один вариант выделиться.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=350)


# --------------------------
#           ТРЕНДЫ
# --------------------------

def ai_trends(query: str, premium: bool) -> str:
    system_prompt = (
        "Ты аналитик трендов e-commerce. "
        "Дай стратегический взгляд, не выдумывай конкретных цифр."
    )

    if premium:
        user_prompt = f"""
Полный обзор трендов:

{query}

1) 5–10 актуальных трендов.
2) Почему каждый тренд растёт.
3) Какие товары подходят под тренд.
4) Какие тренды перегреты.
5) Где окно возможностей.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)

    else:
        user_prompt = f"""
Краткий список трендов:

{query}

1) 2–3 тренда.
2) Одно предложение — суть каждого.
3) Одна рекомендация, как использовать тренды.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=350)


# --------------------------
#         ИДЕИ ТОВАРОВ
# --------------------------

def ai_ideas(query: str, premium: bool) -> str:
    system_prompt = (
        "Ты продакт-менеджер и предприниматель. "
        "Генерируешь идеи под опыт и интересы человека."
    )

    if premium:
        user_prompt = f"""
Полный список идей на основе запроса:

{query}

1) Портрет человека.
2) 8–15 идей товаров.
3) Для каждой: формат продаж, чек, аудитория, плюс и минус.
4) 1–3 приоритетные идеи.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)

    else:
        user_prompt = f"""
Демо-режим идей:

{query}

1) 1 предложение — какой тип предпринимателя.
2) 3–5 идей.
3) Каждую идею поясни 1 предложением.
"""
        return _call_openai(system_prompt, user_prompt, max_tokens=350)


# --------------------------
#   ПРЕМИУМ АНАЛИЗ НИШИ / ТОВАРА
# --------------------------

def ai_premium_analyze(query: str) -> str:
    system_prompt = (
        "Ты senior-аналитик товарного бизнеса. "
        "Делаешь глубокий профессиональный разбор ниши или товара."
    )

    user_prompt = f"""
Подробный премиум-анализ:

{query}

1) Стоит ли заходить и при каких условиях.
2) Целевая аудитория.
3) Конкуренция и позиционирование.
4) Пример математики (логика, без цифр).
5) Риски.
6) План теста на 2–4 недели.
"""

    return _call_openai(system_prompt, user_prompt, max_tokens=900)
    # ==========================
#   КАЛЬКУЛЯТОР МАРЖИ
# ==========================

def parse_margin_input(text: str):
    numbers = []
    percent = 0.0

    for part in text.replace(",", ".").split():
        part = part.strip()
        if not part:
            continue

        if part.endswith("%"):
            try:
                percent = float(part[:-1])
            except ValueError:
                continue
        else:
            try:
                numbers.append(float(part))
            except ValueError:
                continue

    if len(numbers) < 2:
        return None, None

    base_cost = sum(numbers[:-1])
    sell_price = numbers[-1]
    fee = percent / 100.0

    return base_cost, sell_price, fee


def calculate_margin(text: str) -> str:
    base_cost, sell_price, fee = parse_margin_input(text)

    if base_cost is None:
        return "Не смог разобрать данные. Отправь несколько чисел (затраты) и последнее число — цену продажи."

    cost_with_fee = base_cost * (1 + fee)
    profit = sell_price - cost_with_fee

    margin_percent = (profit / sell_price * 100) if sell_price > 0 else 0

    return (
        f"Себестоимость (с учётом комиссии): {cost_with_fee:.2f}\n"
        f"Прибыль: {profit:.2f}\n"
        f"Маржа: {margin_percent:.1f}%"
    )


# ==========================
#        ХЕНДЛЕРЫ
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)

    await update.message.reply_text(
        "Привет! Я AI-ассистент предпринимателей.\n"
        "Помогаю с нишами, анализом рынка, конкурентов, трендами и маржей.\n\n"
        "Выберите язык интерфейса:",
        reply_markup=keyboard_lang(),
    )


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        LOCALES["ru"]["menu"],
        reply_markup=keyboard_user("ru"),
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    user_id = user.id

    t = LOCALES["ru"]

    # Берём данные пользователя
    data = get_user_data(user_id)
    if not data:
        register_user(user)
        data = get_user_data(user_id)

    increment_requests(user_id)

    role = data["role"]
    is_premium = bool(data["premium_until"] and data["premium_until"] > time.time())
    mode = context.user_data.get("mode")

    # ---------------------------
    #   РЕЖИМЫ ВВОДА ТЕКСТА
    # ---------------------------

    if mode == "niche":
        context.user_data["mode"] = None
        await update.message.chat.send_action(ChatAction.TYPING)

        result = ai_niche(text, premium=is_premium)

        if not is_premium:
            result += (
                "\n\n<b>Это демо-версия.</b>\n"
                "Хочешь полный отчёт по нишам? Нажми «⭐ Купить Premium»."
            )

        await update.message.reply_text(result, parse_mode="HTML")
        return

    if mode == "market":
        context.user_data["mode"] = None
        await update.message.chat.send_action(ChatAction.TYPING)

        result = ai_market(text, premium=is_premium)

        if not is_premium:
            result += (
                "\n\n<b>Это демо.</b>\n"
                "Полный анализ рынка доступен в Premium-доступе — «⭐ Купить Premium»."
            )

        await update.message.reply_text(result, parse_mode="HTML")
        return

    if mode == "competitors":
        context.user_data["mode"] = None
        await update.message.chat.send_action(ChatAction.TYPING)

        result = ai_competitors(text, premium=is_premium)

        if not is_premium:
            result += (
                "\n\n<b>Это демо.</b>\n"
                "Полный анализ конкурентов доступен в Premium."
            )

        await update.message.reply_text(result, parse_mode="HTML")
        return

    if mode == "trends":
        context.user_data["mode"] = None
        await update.message.chat.send_action(ChatAction.TYPING)

        result = ai_trends(text, premium=is_premium)

        if not is_premium:
            result += (
                "\n\n<b>Это демо.</b>\n"
                "Полная тренд-аналитика доступна в Premium."
            )

        await update.message.reply_text(result, parse_mode="HTML")
        return

    if mode == "ideas":
        context.user_data["mode"] = None
        await update.message.chat.send_action(ChatAction.TYPING)

        result = ai_ideas(text, premium=is_premium)

        if not is_premium:
            result += (
                "\n\n<b>Это демо.</b>\n"
                "Расширенные идеи доступны только в Premium."
            )

        await update.message.reply_text(result, parse_mode="HTML")
        return

    if mode == "ai_premium":
        context.user_data["mode"] = None

        if not is_premium:
            await update.message.reply_text(t["no_premium"])
            return

        await update.message.chat.send_action(ChatAction.TYPING)
        result = ai_premium_analyze(text)
        await update.message.reply_text(result, parse_mode="HTML")
        return

    if mode == "margin":
        context.user_data["mode"] = None
        result = calculate_margin(text)
        await update.message.reply_text(result)
        return

    # ---------------------------
    #      КНОПКИ ПОЛЬЗОВАТЕЛЯ
    # ---------------------------

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
        await update.message.reply_text(t["ask_margin"])
        return

    if text == t["btn_ai"]:
        if not is_premium:
            await update.message.reply_text(t["no_premium"], parse_mode="HTML")
            return
        context.user_data["mode"] = "ai_premium"
        await update.message.reply_text(t["ask_ai"])
        return

    if text == t["btn_cabinet"]:
        premium_until = data["premium_until"]

        if premium_until and premium_until > time.time():
            dt_str = time.strftime("%d.%m.%Y", time.localtime(premium_until))
            prem_text = t["premium_active_until"].format(dt=dt_str)
        else:
            prem_text = t["premium_not_active"]

        msg = t["cabinet_template"].format(
            user_id=user_id,
            role=role,
            premium_until=prem_text,
            requests=data["request_count"],
        )

        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if text == t["btn_buy"]:
        await update.message.reply_text(
            """
⭐ ТАРИФЫ PREMIUM:

Обычные цены:
• 1 месяц — 490 сом
• 6 месяцев — 1990 сом
• 1 год — 3490 сом

🔥 АКЦИЯ (до конца месяца):
• 1 месяц — 390 сом
• 6 месяцев — 1690 сом
• 1 год — 2990 сом

После оплаты отправьте чек менеджеру: @Artbazar_support
""".strip()
        )
        return
      # ---------------------------
    #      КНОПКИ МЕНЕДЖЕРА
    # ---------------------------

    if text == t["btn_manager_give"] and role in ("manager", "owner"):
        context.user_data["mode"] = "manager_givepremium"
        await update.message.reply_text(
            "Пришли ID пользователя и количество месяцев премиума.\n"
            "Пример: 123456789 1"
        )
        return

    if text == t["btn_manager_stats"] and role in ("manager", "owner"):
        new_users, active_users, new_prem = get_stats_24h()

        await update.message.reply_text(
            f"📊 Статистика за 24 часа:\n\n"
            f"Новых пользователей: {new_users}\n"
            f"Активных пользователей: {active_users}\n"
            f"Выдач премиума: {new_prem}\n"
        )
        return


    # ---------------------------
    #      КНОПКИ ВЛАДЕЛЬЦА
    # ---------------------------

    if text == t["btn_owner_stats"] and role == "owner":
        all_users, active_premium, total_premium_events = get_full_stats()
        await update.message.reply_text(
            f"📊 Полная статистика:\n\n"
            f"Всего пользователей: {all_users}\n"
            f"Активных премиум: {active_premium}\n"
            f"Всего выдач премиума: {total_premium_events}\n"
        )
        return

    if text == t["btn_owner_managers"] and role == "owner":
        await update.message.reply_text(
            "Список менеджеров:\n"
            f"• @{DEFAULT_MANAGER_USERNAME} — ID {DEFAULT_MANAGER_ID}\n\n"
            "Управление менеджерами пока в разработке."
        )
        return


    # ---------------------------
    #         ФОЛБЭК
    # ---------------------------

    await update.message.reply_text(
        "Я не понял запрос. Выбери действие из меню или задай вопрос понятнее."
    )


# ==========================
#    КОМАНДЫ /setmanager
# ==========================

async def set_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Команда доступна только владельцу.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Использование: /setmanager <user_id>")
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id должен быть числом.")
        return

    set_role(uid, "manager")

    await update.message.reply_text(
        f"Пользователь {uid} назначен менеджером."
    )


# ==========================
#     КОМАНДА /setowner
# ==========================

async def set_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Команда доступна только владельцу.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Использование: /setowner <user_id>")
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id должен быть числом.")
        return

    set_role(uid, "owner")

    await update.message.reply_text(
        f"Пользователь {uid} назначен владельцем."
    )


# ==========================
#      ЗАПУСК WEBHOOK
# ==========================

def main():
    init_db()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setmanager", set_manager))
    application.add_handler(CommandHandler("setowner", set_owner))

    application.add_handler(
        MessageHandler(filters.Regex("Кыргызча|Қазақша|Русский"), choose_lang)
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle)
    )

    # Запуск webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{APP_URL}/{TOKEN}",
    )


if __name__ == "__main__":
    main()
