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

TOKEN = os.getenv("BOT_TOKEN", "ТОКЕН_ТУТ")
APP_URL = os.getenv("APP_URL", "https://artbazarbot.fly.dev")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DB_PATH = "artbazarbot.db"

OWNER_ID = 1974482384  # Тилек
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
        SELECT user_id, username, first_name, role, premium_until, created_at, last_active, request_count
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
        SET request_count = COALESCE(request_count, 0) + 1,
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
    c.execute(
        """
        UPDATE users SET role = ? WHERE user_id = ?
        """,
        (role, user_id),
    )
    conn.commit()
    conn.close()


def give_premium(user_id: int, months: int, manager_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = int(time.time())
    delta = months * PREMIUM_ONE_MONTH

    c.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    current_until = row[0] if row and row[0] else 0
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
    day_ago = now - 24 * 60 * 60

    c.execute(
        """
        SELECT COUNT(*) FROM users WHERE created_at >= ?
        """,
        (day_ago,),
    )
    new_users = c.fetchone()[0]

    c.execute(
        """
        SELECT COUNT(*) FROM users WHERE last_active >= ?
        """,
        (day_ago,),
    )
    active_users = c.fetchone()[0]

    c.execute(
        """
        SELECT COUNT(*) FROM premium_logs WHERE created_at >= ?
        """,
        (day_ago,),
    )
    new_premium = c.fetchone()[0]

    conn.close()
    return new_users, active_users, new_premium


def get_full_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    now = int(time.time())
    c.execute(
        "SELECT COUNT(*) FROM users WHERE premium_until > ?",
        (now,),
    )
    total_premium = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM premium_logs")
    total_premium_events = c.fetchone()[0]

    conn.close()
    return total_users, total_premium, total_premium_events


# ==========================
#      ТЕКСТЫ / ЛОКАЛИ
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
        "btn_manager_give": "⭐ Выдать премиум",
        "btn_manager_stats": "📊 Статистика (24 ч)",
        "btn_owner_stats": "📊 Полная статистика",
        "btn_owner_managers": "👨‍💼 Менеджеры",
        "not_allowed": "У вас нет доступа к этой команде.",
        "ask_niche": (
            "Расскажи, какой у тебя опыт, стартовый бюджет, страна/город и где хочешь продавать "
            "(маркетплейс, Instagram, офлайн и т.п.).\n\n"
            "Напиши всё в одном сообщении — я подберу ниши с плюсами и рисками."
        ),
        "ask_market": (
            "Опиши рынок, который тебя интересует.\n\n"
            "Например: «одежда для мам в Казахстане через Instagram» или «товары для животных на Ozon»."
        ),
        "ask_competitors": (
            "Отправь ссылки или описания конкурентов (Instagram, маркетплейсы, сайты). "
            "Я разберу их сильные и слабые стороны."
        ),
        "ask_trends": (
            "Напиши категорию, страну/регион и формат (маркетплейс, офлайн, Instagram и т.п.). "
            "Я дам обзор трендов."
        ),
        "ask_ideas": (
            "Расскажи о себе: опыт, интересы, что нравится/не нравится продавать, какие бюджеты.\n\n"
            "Я предложу идеи товаров и направлений."
        ),
        "ask_margin": (
            "Отправь данные в формате:\n\n"
            "Закуп: 350\n"
            "Доставка до склада: 70\n"
            "Комиссия маркетплейса: 15%\n"
            "Желаемая наценка: 2.3\n\n"
            "Или просто перечисли числа и проценты в свободной форме."
        ),
        "ask_ai": (
            "Опиши товар или нишу, которую хочешь разложить по полочкам. "
            "Я сделаю глубокий разбор (Premium)."
        ),
        "no_premium": (
            "Этот режим доступен только для Premium.\n\n"
            "Оформи подписку через «⭐ Купить Premium», чтобы получить полный доступ."
        ),
        "cabinet_template": (
            "<b>Твой кабинет:</b>\n\n"
            "ID: {user_id}\n"
            "Роль: {role}\n"
            "Premium до: {premium_until}\n"
            "Запросов к боту: {requests}\n"
        ),
        "premium_active_until": "Премиум активен до: {dt}",
        "premium_not_active": "Премиум ещё не подключён.",
    }
}


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


def ai_niche(query: str, premium: bool) -> str:
    """
    Подбор ниши: в бесплатной версии — укороченный ответ, в премиум — полный отчёт.
    """
    system_prompt = (
        "Ты бизнес-аналитик и продуктолог. Помогаешь предпринимателям подбирать ниши под их опыт, бюджет и рынок. "
        "Отвечай структурно, по делу, без воды."
    )

    if premium:
        user_prompt = f"""Данные о запросе на подбор ниши:
{query}

Сформируй ПОЛНЫЙ профессиональный отчёт:
1) Краткий профиль предпринимателя.
2) 5–7 конкретных ниш (название + формат продаж).
3) Для каждой ниши: плюсы, риски, пример цен/чека, пример воронки продаж.
4) Пример юнит-экономики на 1–2 нишах.
5) Какую нишу рекомендовать на старт и почему.
6) Первые шаги на 2–4 недели (пошаговый план)."""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)
    else:
        user_prompt = f"""Данные о запросе на подбор ниши:
{query}

Сделай КРАТКИЙ обзор (для демо-версии):
1) Кто предприниматель (1–2 предложения).
2) 2–3 возможные ниши.
3) Для каждой ниши: по 1 плюсу и 1 риску.
4) Какую нишу логично протестировать первой.
Пиши сжато, чтобы текст поместился в одном экране телефона."""
        return _call_openai(system_prompt, user_prompt, max_tokens=450)


def ai_market(query: str, premium: bool) -> str:
    """
    Анализ рынка: free — поверхностный, premium — глубокий.
    """
    system_prompt = (
        "Ты эксперт по анализу рынков в СНГ. Учитываешь платёжеспособность, конкуренцию, формат продаж и т.п. "
        "Отвечай структурно и практично."
    )

    if premium:
        user_prompt = f"""Исходные данные для глубокого анализа рынка:
{query}

Подготовь развёрнутый отчёт:
1) Обзор рынка и ёмкость (качественно, без выдуманных цифр).
2) Портрет ключевых сегментов клиентов.
3) Типичные уровни цен и чеков.
4) Уровень конкуренции и барьеры входа.
5) Основные риски.
6) Практические рекомендации по заходу на рынок.
7) Стратегия теста на 2–4 недели."""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)
    else:
        user_prompt = f"""Исходные данные для анализа рынка:
{query}

Сделай КРАТКИЙ обзор (демо-версия):
1) В двух-трёх предложениях опиши состояние рынка.
2) Кто основной клиент.
3) Какой общий уровень конкуренции (низкий/средний/высокий).
4) Один главный риск и один главный плюс для входа.
Пиши компактно, чтобы текст поместился в один экран."""
        return _call_openai(system_prompt, user_prompt, max_tokens=450)


def ai_competitors(query: str, premium: bool) -> str:
    """
    Анализ конкурентов: free — кратко, premium — с позиционированием и стратегией.
    """
    system_prompt = (
        "Ты специалист по конкурентному анализу. Разбираешь сильные и слабые стороны конкурентов "
        "и предлагаешь стратегию дифференциации."
    )

    if premium:
        user_prompt = f"""Описание конкурентов:
{query}

Сделай полный конкурентный анализ:
1) Кто конкуренты и какие продукты/ниши закрывают.
2) Их сильные стороны.
3) Их слабые места.
4) Потенциальные точки дифференциации для нашего проекта.
5) Рекомендации по позиционированию.
6) Ошибки, которых стоит избегать."""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)
    else:
        user_prompt = f"""Описание конкурентов:
{query}

Сделай короткий разбор (демо):
1) В двух-трёх предложениях опиши общую картину конкуренции.
2) Назови одну сильную сторону рынка и одну слабую.
3) Дай одну идею, как можно выделиться.
Пиши кратко."""
        return _call_openai(system_prompt, user_prompt, max_tokens=450)


def ai_trends(query: str, premium: bool) -> str:
    """
    Анализ трендов: free — 2–3 тренда, premium — развёрнутый список и рекомендации.
    """
    system_prompt = (
        "Ты аналитик по трендам в e-commerce и онлайн-бизнесе. Указывай, что это стратегический взгляд, "
        "а не точные данные с маркетплейсов."
    )

    if premium:
        user_prompt = f"""Запрос по трендам:
{query}

Сделай развёрнутый отчёт:
1) 5–10 актуальных трендов в этой категории/регионе.
2) Почему каждый из трендов появился и за счёт чего держится.
3) Какие форматы товаров/услуг хорошо заходят под эти тренды.
4) Какие тренды уже перегреты.
5) Где остаётся окно возможностей для новичка."""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)
    else:
        user_prompt = f"""Запрос по трендам:
{query}

Сделай краткий обзор (демо):
1) Назови 2–3 актуальных тренда.
2) К каждому добавь по одному предложению — в чём суть.
3) Дай одну общую рекомендацию, как использовать эти тренды."""
        return _call_openai(system_prompt, user_prompt, max_tokens=450)


def ai_ideas(query: str, premium: bool) -> str:
    """
    Идеи товаров/направлений: free — 3–5 идей, premium — до 15 с деталями.
    """
    system_prompt = (
        "Ты продакт-менеджер и предприниматель. Генерируешь идеи товаров/направлений под конкретного человека. "
        "Всегда учитывай его опыт, бюджет, интересы и формат продаж."
    )

    if premium:
        user_prompt = f"""Данные о человеке и его запросе на идеи:
{query}

Сделай развёрнутый список идей:
1) Краткий портрет человека.
2) 8–15 идей товаров/направлений.
3) Для каждой идеи: формат продаж, пример чека, пример целевой аудитории, плюс и минус.
4) Выдели 1–3 идеи как приоритетные на старт и объясни, почему."""
        return _call_openai(system_prompt, user_prompt, max_tokens=900)
    else:
        user_prompt = f"""Данные о человеке и его запросе на идеи:
{query}

Сделай краткую демо-выдачу:
1) В одном-двух предложениях опиши, какой это тип предпринимателя.
2) Предложи 3–5 идей товаров/направлений.
3) К каждой идее добавь по одному предложению с пояснением."""
        return _call_openai(system_prompt, user_prompt, max_tokens=450)


def ai_premium_analyze(query: str) -> str:
    """
    Отдельная премиальная функция: глубокий разбор одной ниши или товара.
    Доступна только для пользователей с Premium.
    """
    system_prompt = (
        "Ты senior-аналитик по товарному бизнесу и маркетплейсам. "
        "Делаешь глубокий разбор товара или ниши для предпринимателя из СНГ."
    )
    user_prompt = f"""Объект для анализа (товар или ниша):
{query}

Нужно:
1) Резюме — стоит ли заходить и при каких условиях.
2) Описание целевой аудитории.
3) Конкуренция и возможное позиционирование.
4) Пример базовой математики (без выдуманных точных цифр, только логика).
5) Ключевые риски.
6) Пошаговый план теста на 2–4 недели."""
    return _call_openai(system_prompt, user_prompt, max_tokens=900)


# ==========================
#      КАЛЬКУЛЯТОР МАРЖИ
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
        return "Не смог разобрать данные. Пришли несколько чисел (затраты) и последнее число — цена продажи."

    cost_with_fee = base_cost * (1 + fee)
    profit = sell_price - cost_with_fee
    if sell_price > 0:
        margin_percent = profit / sell_price * 100
    else:
        margin_percent = 0.0

    return (
        f"Себестоимость (с учётом комиссии): {cost_with_fee:.2f}\n"
        f"Прибыль с единицы: {profit:.2f}\n"
        f"Маржа: {margin_percent:.1f}%"
    )


# ==========================
#      ХЕНДЛЕРЫ
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)

    await update.message.reply_text(
        "Привет! Я AI-ассистент для предпринимателей. Помогаю с нишами, анализом рынка и маржей.\n\n"
        "Сначала выбери язык (пока работает только русский интерфейс).",
        reply_markup=keyboard_lang(),
    )


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        LOCALES["ru"]["menu"],
        reply_markup=keyboard_user("ru"),
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
    is_premium = bool(data["premium_until"] and data["premium_until"] > time.time())
    mode = context.user_data.get("mode")

    # ====== режим выдачи премиума менеджером/владельцем ======
    if mode == "manager_givepremium" and role in ("manager", "owner"):
        context.user_data["mode"] = None
        try:
            months = int(text.strip())
            new_until = give_premium(
                context.user_data["target_user_id"], months, user_id
            )
            dt_str = time.strftime("%d.%m.%Y", time.localtime(new_until))
            await update.message.reply_text(f"Премиум выдан до {dt_str}.")
        except Exception:
            await update.message.reply_text("Не получилось выдать премиум. Проверь ввод.")
        return

    # ====== AI режимы ======
    if mode == "niche":
        context.user_data["mode"] = None
        try:
            await update.message.chat.send_action(action=ChatAction.TYPING)
            result = ai_niche(text, premium=is_premium)
            if not is_premium:
                result += (
                    "\n\n— — —\n\n"
                    "<b>Это демо-ответ.</b> Полную аналитику по нишам даю в Premium-доступе.\n"
                    "Нажми «⭐ Купить Premium», чтобы получить
