# handlers.py

from aiogram import Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import save_user, update_last_active
from premium import check_premium

router = Router()


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подбор ниши")],
            [KeyboardButton(text="Маржа")],
            [KeyboardButton(text="Конкуренты")],
            [KeyboardButton(text="Премиум 🔐")]
        ],
        resize_keyboard=True
    )


@router.message()
async def all_messages(message: types.Message):
    user = message.from_user
    save_user(user.id, user.username, user.first_name)
    update_last_active(user.id)

    txt = message.text.lower()

    if txt == "подбор ниши":
        await message.answer("Идёт подбор ниши…", reply_markup=main_menu())

    elif txt == "маржа":
        await message.answer("Калькулятор маржи активирован.", reply_markup=main_menu())

    elif txt == "конкуренты":
        await message.answer("Анализ конкурентов запускаю…", reply_markup=main_menu())

    elif txt == "премиум 🔐":
        if check_premium(user.id):
            await message.answer("У тебя *Премиум активен*! 🔥", reply_markup=main_menu())
        else:
            await message.answer("Премиум не активен. Для подключения — напишите менеджеру.")

    else:
        await message.answer("Выбери команду на клавиатуре.", reply_markup=main_menu())
