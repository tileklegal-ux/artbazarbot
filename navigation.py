from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards import get_main_keyboard
from roles_db import get_role
from utils import get_text

# Клавиатура для локальной навигации внутри каких-то процессов (если понадобится)
navigation_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Назад")],
        [KeyboardButton(text="🏠 Главное меню")],
    ],
    resize_keyboard=True,
)


async def go_main_menu(message):
    """Переход в главное меню по роли пользователя, с мультиязычным заголовком."""
    user_id = message.from_user.id
    role = get_role(user_id)
    kb = get_main_keyboard(role)

    # Текст берём из messages_xx: "Главное меню:" / аналог на KG/KZ
    await message.answer(get_text(user_id, "menu_title"), reply_markup=kb)


async def go_back(message, state):
    """Выход из текущего FSM-состояния и возврат в главное меню."""
    await state.clear()
    await go_main_menu(message)
