from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import create_or_update_user, get_user, set_language
from utils import get_texts, ask_openai

router = Router()

@router.message(F.text == "/start")
async def start(message: Message):
    user_id = message.from_user.id
    create_or_update_user(user_id, message.from_user.username, message.from_user.first_name)

    user = get_user(user_id)
    texts = get_texts(user["language"])

    await message.answer(texts["welcome"], reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang_"))
async def lang_change(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    set_language(callback.from_user.id, lang)

    texts = get_texts(lang)
    await callback.message.edit_text(texts["language_changed"], reply_markup=main_keyboard(lang))


@router.callback_query(F.data == "niche")
async def niche(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["niche_placeholder"])
    response = await ask_openai(user["language"], "Подбор ниши для бизнеса")
    await callback.message.answer(response)


@router.callback_query(F.data == "market")
async def market(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["market_placeholder"])
    response = await ask_openai(user["language"], "Анализ рынка")
    await callback.message.answer(response)


@router.callback_query(F.data == "competitors")
async def competitors(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["competitors_placeholder"])
    response = await ask_openai(user["language"], "Анализ конкурентов")
    await callback.message.answer(response)


@router.callback_query(F.data == "margin_calc")
async def margin(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["margin_placeholder"])
    response = await ask_openai(user["language"], "Калькулятор маржи")
    await callback.message.answer(response)


@router.callback_query(F.data == "ideas")
async def ideas(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["ideas_placeholder"])
    response = await ask_openai(user["language"], "Генератор идей для бизнеса")
    await callback.message.answer(response)


def main_keyboard(lang):
    texts = get_texts(lang)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts["btn_niche"], callback_data="niche")],
            [InlineKeyboardButton(text=texts["btn_market"], callback_data="market")],
            [InlineKeyboardButton(text=texts["btn_competitors"], callback_data="competitors")],
            [InlineKeyboardButton(text=texts["btn_margin"], callback_data="margin_calc")],
            [InlineKeyboardButton(text=texts["btn_ideas"], callback_data="ideas")],
            [InlineKeyboardButton(text=texts["btn_language"], callback_data="lang_menu")],
        ]
    )


def language_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang_kg")],
            [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz")],
        ]
    )
