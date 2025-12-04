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

# ==========================
#          CONFIG
# ==========================
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = "database.db"

OWNER_ID = 1974482384          # твой ID как владельца
MANAGER_USERNAME = "Artbazar_support"

client = OpenAI(api_key=OPENAI_KEY)


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
    },
}


def format_time(ts):
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ==========================
#        КЛАВИАТУРЫ
# ==========================
def keyboard_main(lang: str = "ru"):
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
        resize_keyboard=True
    )


def keyboard_lang():
    return ReplyKeyboardMarkup(
        [
            ["🇰🇬 Кыргызча", "🇰🇿 Қазақша"],
            ["🇷🇺 Русский"],
        ],
        resize_keyboard=True
    )


# ==========================
#      AI-ПОМОЩНИКИ
# ==========================
def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """Общий хелпер для всех аналитик."""
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
        "Ты бизнес-аналитик и продуктолог. Помогаешь начинающим и действующим предпринимателям "
        "подбирать ниши под их опыт, бюджет и рынок. Отвечай структурно, по делу, без воды. "
        "Учитывай риски, конкуренцию, маржинальность и сложность запуска."
    )
    user = (
        "Данные о запросе на подбор ниши:\n"
        f"{query}\n\n"
        "Сформируй ответ по структуре:\n"
        "1) Кратко профиль предпринимателя (1–2 строки).\n"
        "2) 3–7 конкретных ниш (название + формат продаж).\n"
        "3) Для каждой ниши: плюсы, риски, пример цен/чека, пример воронки продаж.\n"
        "4) Какую нишу ты бы рекомендовал начать тестировать первой и почему.\n"
    )
    return _call_openai(system, user)


def ai_market(query: str) -> str:
    system = (
        "Ты эксперт по анализу рынков в СНГ. Учитываешь платёжеспособность, конкуренцию, формат продаж, "
        "логистику и онлайн/офлайн поведение покупателей. Пишешь без воды, с выводами и рекомендациями."
    )
    user = (
        "Исходные данные для анализа рынка:\n"
        f"{query}\n\n"
        "Сделай:\n"
        "1) Обзор рынка (объём/стадия, рост или стагнация, на чём зарабатывают игроки).\n"
        "2) Портрет клиента (кто покупает, боли, мотивация, частота покупок).\n"
        "3) Оценка конкуренции (насыщенность, уровень демпинга, чем можно отличаться).\n"
        "4) Риски и барьеры входа.\n"
        "5) Практические рекомендации: с чего зайти на рынок при небольшом бюджете.\n"
    )
    return _call_openai(system, user)


def ai_competitors(query: str) -> str:
    system = (
        "Ты специалист по конкурентному анализу. Умеешь разбирать сильные и слабые стороны конкурентов "
        "и предлагать стратегию дифференциации. Пиши конкретно, без общих фраз."
    )
    user = (
        "Описание конкурентов:\n"
        f"{query}\n\n"
        "Дай анализ по структуре:\n"
        "1) Таблично/структурно: кто конкуренты и что предлагают (формат, ЦА, ценовой сегмент).\n"
        "2) Их сильные стороны.\n"
        "3) Их слабые места и недоработки.\n"
        "4) Возможные точки дифференциации для нашего проекта (что сделать иначе/лучше).\n"
        "5) Рекомендации по позиционированию и офферам.\n"
    )
    return _call_openai(system, user)


def ai_trends(query: str) -> str:
    system = (
        "Ты аналитик по трендам в e-commerce и онлайн-сервисах. "
        "Не имеешь доступа к реальному времени, поэтому опираешься на общую картину, "
        "известные изменения спроса и здравый смысл. Всегда честно указывай, что это не точные данные "
        "по конкретным маркетплейсам, а стратегический взгляд."
    )
    user = (
        "Запрос по трендам:\n"
        f"{query}\n\n"
        "Нужно:\n"
        "1) Описать 5–10 актуальных трендов в этой категории/регионе.\n"
        "2) Пояснить, почему они появились (поведение людей, технологии, экономика).\n"
        "3) Какие товарные категории или форматы услуг логично заходят под эти тренды.\n"
        "4) Какие тренды выглядят перегретыми и где есть ещё окно возможностей.\n"
    )
    return _call_openai(system, user)


def ai_ideas(query: str) -> str:
    system = (
        "Ты продакт-менеджер и предприниматель. Помогаешь генерировать идеи товаров и направлений "
        "под конкретного человека и его ограничений. Учитывай опыт, интересы, бюджет и рынок."
    )
    user = (
        "Данные о человеке и его запросе на идеи:\n"
        f"{query}\n\n"
        "Сделай:\n"
        "1) Краткий портрет (человек, ресурсы, ограничения).\n"
        "2) 5–15 идей товаров/направлений с коротким описанием.\n"
        "3) Для каждой идеи: формат продаж, пример чека, плюс/минус по сложности.\n"
        "4) Какие 1–2 идеи лучше всего подойдут на старт и почему.\n"
    )
    return _call_openai(system, user)


def ai_premium_analyze(query: str) -> str:
    system = (
        "Ты senior-аналитик по товарному бизнесу и маркетплейсам. "
        "Делаешь глубокий разбор одного товара или ниши: цифры примерные, но логика должна быть очень сильной. "
        "Пиши структурно и по делу, как платный консалтинг."
    )
    user = (
        "Объект для анализа (товар или ниша):\n"
        f"{query}\n\n"
        "Нужно:\n"
        "1) Краткое резюме — стоит ли вообще лезть.\n"
        "2) Спрос и ЦА.\n"
        "3) Конкуренция и варианты позиционирования.\n"
        "4) Пример математики (примерные цены, маржа, чек).\n"
        "5) Риски.\n"
        "6) Пошаговый план теста ниши на ближайшие 2–4 недели.\n"
    )
    return _call_openai(system, user, max_tokens=800)


# ==========================
#      КАЛЬКУЛЯТОР МАРЖИ
# ==========================
def _parse_number(text: str):
    """Пытаемся аккуратно распарсить число из строки."""
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
        return str(round(x, 2)).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)

    verdict = "🟡 Средняя маржа, можно тестировать, но смотри по конкуренции."
    if profit <= 0:
        verdict = "🔴 Маржа отрицательная или нулевая — в таком виде товар невыгоден."
    elif margin_percent >= 30 and roi >= 50:
        verdict = "🟢 Хорошая маржа, товар перспективный."
    elif margin_percent < 15:
        verdict = "🟠 Маржа слабая. Нужна более высокая цена или более дешёвая закупка."

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


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # пока просто показываем русское меню
    await update.message.reply_text(
        LOCALES["ru"]["menu"],
        reply_markup=keyboard_main()
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text or ""
    t = LOCALES["ru"]

    # гарантируем, что юзер есть в БД
    data = get_user_data(user_id)
    if not data:
        register_user(user)
        data = get_user_data(user_id)

    increment_requests(user_id)

    mode = context.user_data.get("mode")

    # ---------- РЕЖИМ КАЛЬКУЛЯТОРА МАРЖИ ----------
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
                "Теперь введи цену продажи (за сколько планируешь продавать товар).\n"
                "Например: 1500"
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

    # ---------- AI-РЕЖИМЫ (НИША / РЫНОК / КОНКУРЕНТЫ / ТРЕНДЫ / ИДЕИ / PREMIUM) ----------
    if mode == "niche":
        context.user_data["mode"] = None
        try:
            result = ai_niche(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Не удалось проанализировать нишу. Проверь OpenAI-ключ.")
        return

    if mode == "market":
        context.user_data["mode"] = None
        try:
            result = ai_market(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка при анализе рынка. Проверь OpenAI-ключ.")
        return

    if mode == "competitors":
        context.user_data["mode"] = None
        try:
            result = ai_competitors(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка при анализе конкурентов. Проверь OpenAI-ключ.")
        return

    if mode == "trends":
        context.user_data["mode"] = None
        try:
            result = ai_trends(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text(
                "Не удалось получить трендовую аналитику. Проверь OpenAI-ключ."
            )
        return

    if mode == "ideas":
        context.user_data["mode"] = None
        try:
            result = ai_ideas(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка при генерации идей. Проверь OpenAI-ключ.")
        return

    if mode == "ai_premium":
        context.user_data["mode"] = None
        try:
            result = ai_premium_analyze(text)
            await update.message.reply_text(result)
        except Exception:
            await update.message.reply_text("Ошибка AI-анализа. Проверь OpenAI-ключ.")
        return

    # ---------- КНОПКИ МЕНЮ ----------
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
        # проверка премиума
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
        await update.message.reply_text(profile, reply_markup=keyboard_main())
        return

    if text == t["btn_buy"]:
        await upd
