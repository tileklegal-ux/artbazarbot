from aiogram import Router, types
from aiogram.filters import Command
from messages_ru import texts as ru
from messages_kz import texts as kz
from messages_kg import texts as kg

router = Router()

LANGUAGES = {
    "ru": ru,
    "kz": kz,
    "kg": kg
}

@router.message(Command("start"))
async def start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Русский 🇷🇺"),
         types.KeyboardButton(text="Қазақша 🇰🇿"),
         types.KeyboardButton(text="Кыргызча 🇰🇬")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(
        "Выберите язык / Тілді таңдаңыз / Тилди тандаңыз:",
        reply_markup=keyboard
    )


@router.message()
async def language_select(message: types.Message):

    if message.text == "Русский 🇷🇺":
        lang = LANGUAGES["ru"]

    elif message.text == "Қазақша 🇰🇿":
        lang = LANGUAGES["kz"]

    elif message.text == "Кыргызча 🇰🇬":
        lang = LANGUAGES["kg"]

    else:
        return await message.answer("Пожалуйста, выберите язык через меню.")

    menu_kb = [
        [types.KeyboardButton(text=lang["button_market"])],
        [types.KeyboardButton(text=lang["button_niche"])],
        [types.KeyboardButton(text=lang["button_profit"])],
        [types.KeyboardButton(text=lang["button_recommend"])],
        [types.KeyboardButton(text=lang["button_premium"])]
    ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=menu_kb, resize_keyboard=True)

    await message.answer(lang["welcome"], reply_markup=keyboard)
