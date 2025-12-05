import logging
from aiogram import Router, F
from aiogram.types import Message
from openai import OpenAI
from config import OPENAI_KEY
from database import set_user_language, get_user_language

router = Router()
client = OpenAI(api_key=OPENAI_KEY)

# -----------------------------
#  ЧЕЛОВЕЧЕСКИЙ SYSTEM PROMPT
# -----------------------------
SYSTEM_PROMPT = (
    "Ты — AI-ассистент для предпринимателей. "
    "Отвечай простым человеческим языком, будто объясняешь другу-предпринимателю. "
    "Не используй Markdown, не используй ###, *, списки 1) 2) 3). "
    "Пиши абзацами. "
    "Стиль — живой, уверенный, спокойный, по делу. "
    "Сегменты ответа: "
    "Спрос: ... "
    "Конкуренция: ... "
    "Маржа (если уместно): ... "
    "Рекомендации: ... "
    "Избегай канцелярита, сухих текстов и академического стиля. "
    "Пиши так, чтобы читать было приятно и полезно."
)

# -----------------------------
# КОМАНДА /start
# -----------------------------
@router.message(F.text == "/start")
async def start_cmd(msg: Message):
    await msg.answer(
        "Добро пожаловать в ArtBazar AI — ассистент для продавцов онлайн.\n\n"
        "Выберите язык / Тилди тандаңыз / Тілді таңдаңыз:",
        reply_markup=create_language_keyboard()
    )

def create_language_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Русский 🇷🇺")],
            [KeyboardButton(text="Кыргызча 🇰🇬")],
            [KeyboardButton(text="Қазақша 🇰🇿")],
        ]
    )


# -----------------------------
# ВЫБОР ЯЗЫКА
# -----------------------------
@router.message(F.text.in_(["Русский 🇷🇺", "Кыргызча 🇰🇬", "Қазақша 🇰🇿"]))
async def choose_language(msg: Message):
    lang = msg.text

    if lang.startswith("Рус"):
        code = "ru"
    elif lang.startswith("Кырг") or lang.startswith("Кыргыз"):
        code = "kg"
    else:
        code = "kz"

    set_user_language(msg.from_user.id, code)

    await msg.answer(
        "Язык сохранён. Выберите функцию:",
        reply_markup=create_menu_keyboard()
    )

def create_menu_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Анализ рынка 📊"), KeyboardButton(text="Подбор ниши 🧭")],
            [KeyboardButton(text="Калькулятор маржи 💰"), KeyboardButton(text="Рекомендации ⚡")],
            [KeyboardButton(text="Премиум 🚀")],
        ]
    )


# -------------------------------------------------
# АНАЛИЗ / НИША / РЕКОМЕНДАЦИИ — ОБРАБОТКА ЗАПРОСА
# -------------------------------------------------
@router.message(F.text.in_(["Анализ рынка 📊", "Подбор ниши 🧭", "Рекомендации ⚡"]))
async def ask_for_description(msg: Message):
    if msg.text.startswith("Анализ рынка"):
        await msg.answer("Опиши товар или нишу, для которой нужен анализ рынка.")
    elif msg.text.startswith("Подбор ниши"):
        await msg.answer("Опиши, чем хочешь заниматься. Бот оценит нишу.")
    else:
        await msg.answer("Расскажи о товаре и ситуации, дам рекомендации по продажам.")


# -----------------------------
# КАЛЬКУЛЯТОР МАРЖИ
# -----------------------------
@router.message(F.text == "Калькулятор маржи 💰")
async def margin_calc(msg: Message):
    await msg.answer("Калькулятор маржи скоро будет доступен в следующем обновлении.")


# -----------------------------
# ПРЕМИУМ
# -----------------------------
@router.message(F.text == "Премиум 🚀")
async def premium(msg: Message):
    await msg.answer("Премиум-функции в разработке. Позже сюда завезём жирные фишки.")


# -----------------------------
# ГЛАВНЫЙ ОБРАБОТЧИК TEKSTA
# -----------------------------
@router.message()
async def ai_response(msg: Message):
    user_text = msg.text
    lang = get_user_language(msg.from_user.id) or "ru"

    # Человекоподобный thinking-ответ
    await msg.answer("Думаю над ответом... Это может занять несколько секунд ⏳")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]
        )

        reply = completion.choices[0].message["content"]

        await msg.answer(reply)

    except Exception as e:
        logging.error(e)
        await msg.answer("Произошла ошибка при обработке запроса. Попробуй ещё раз.")
