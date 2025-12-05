from aiogram import Router, types
from aiogram.filters import Command

from database import get_user_language, set_user_language
from messages_ru import texts as ru
from messages_kz import texts as kz
from messages_kg import texts as kg

router = Router()

LANGS = {"ru": ru, "kz": kz, "kg": kg}

@router.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Русский 🇷🇺"),
             types.KeyboardButton(text="Қазақша 🇰🇿"),
             types.KeyboardButton(text="Кыргызча 🇰🇬")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите язык / Тілді таңдаңыз / Тилди тандаңыз:", reply_markup=keyboard)

@router.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username

    lang = get_user_language(user_id)

    if message.text == "Русский 🇷🇺":
        set_user_language(user_id, username, "ru")
        lang = "ru"
    elif message.text == "Қазақша 🇰🇿":
        set_user_language(user_id, username, "kz")
        lang = "kz"
    elif message.text == "Кыргызча 🇰🇬":
        set_user_language(user_id, username, "kg")
        lang = "kg"

    t = LANGS[lang]

    menu = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=t["button_market"])],
            [types.KeyboardButton(text=t["button_niche"])],
            [types.KeyboardButton(text=t["button_profit"])],
            [types.KeyboardButton(text=t["button_recommend"])],
            [types.KeyboardButton(text=t["button_premium"])],
        ],
        resize_keyboard=True
    )

    await message.answer(t["welcome"], reply_markup=menu)
