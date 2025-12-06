from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards import get_main_keyboard
from roles_db import get_role


# Клавиатура для навигации внутри процессов (FSM и админ-панелей)
navigation_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Назад")],
        [KeyboardButton(text="🏠 Главное меню")],
    ],
    resize_keyboard=True
)


async def go_main_menu(message):
    """Переход в главное меню по роли пользователя."""
    role = get_role(message.from_user.id)
    kb = get_main_keyboard(role)
    await message.answer("🏠 Главное меню", reply_markup=kb)


async def go_back(message, state):
    """Выход из текущего FSM-состояния."""
    await state.clear()
    await go_main_menu(message)
