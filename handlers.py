from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database import get_user_language, set_user_language
from utils import get_text
from ai_service import analyze_market, analyze_niche, give_recommendations

router = Router()

LANG_CALLBACK_PREFIX = "lang_"
user_states: dict[int, str] = {}  # user_id -> "market" / "niche" / "recommend"


@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Русский 🇷🇺", callback_data=f"{LANG_CALLBACK_PREFIX}ru")
    kb.button(text="Кыргызча 🇰🇬", callback_data=f"{LANG_CALLBACK_PREFIX}kg")
    kb.button(text="Қазақша 🇰🇿", callback_data=f"{LANG_CALLBACK_PREFIX}kz")
    kb.adjust(1)

    await message.answer(
        "Выберите язык / Тилди тандаңыз / Тілді таңдаңыз:",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data.startswith(LANG_CALLBACK_PREFIX))
async def set_language(callback: CallbackQuery):
    lang_code = callback.data[len(LANG_CALLBACK_PREFIX):]
    user_id = callback.from_user.id

    set_user_language(user_id, lang_code)

    kb = ReplyKeyboardBuilder()
    kb.button(text=get_text(lang_code, "button_market"))
    kb.button(text=get_text(lang_code, "button_niche"))
    kb.button(text=get_text(lang_code, "button_profit"))
    kb.button(text=get_text(lang_code, "button_recommend"))
    kb.button(text=get_text(lang_code, "button_premium"))
    kb.adjust(2)

    await callback.message.answer(
        get_text(lang_code, "welcome"),
        reply_markup=kb.as_markup(resize_keyboard=True),
    )
    await callback.answer()


@router.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    text = (message.text or "").strip()

    # Обработка меню
    if text == get_text(lang, "button_market"):
        user_states[user_id] = "market"
        await message.answer(get_text(lang, "ask_market"))
        return

    if text == get_text(lang, "button_niche"):
        user_states[user_id] = "niche"
        await message.answer(get_text(lang, "ask_niche"))
        return

    if text == get_text(lang, "button_profit"):
        await message.answer(get_text(lang, "answer_profit_stub"))
        return

    if text == get_text(lang, "button_recommend"):
        user_states[user_id] = "recommend"
        await message.answer(get_text(lang, "ask_recommend"))
        return

    if text == get_text(lang, "button_premium"):
        await message.answer("Премиум-функции в разработке. Позже сюда завезём жирные фишки.")
        return

    # Если пользователь в состоянии AI-анализа
    if user_id in user_states:
        mode = user_states.pop(user_id)
        await message.answer(get_text(lang, "loading"))

        try:
            if mode == "market":
                answer = analyze_market(text, lang)
            elif mode == "niche":
                answer = analyze_niche(text, lang)
            elif mode == "recommend":
                answer = give_recommendations(text, lang)
            else:
                answer = get_text(lang, "unknown_command")

            await message.answer(answer)

        except Exception as e:
            # Для отладки можно логировать e, но пользователю даем человеческий текст
            await message.answer(get_text(lang, "error_ai"))

        return

    # Если ничего не подошло
    await message.answer(get_text(lang, "unknown_command"))
