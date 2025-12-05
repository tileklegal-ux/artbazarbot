from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from roles_db import ROLE_OWNER, ROLE_MANAGER, ROLE_USER


# ---------- выбор языка ----------
language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Русский 🇷🇺")],
        [KeyboardButton(text="Кыргызча 🇰🇬")],
        [KeyboardButton(text="Қазақша 🇰🇿")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ---------- главные меню по ролям ----------

def _user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Анализ рынка 📊"),
                KeyboardButton(text="Подбор ниши 🧭"),
            ],
            [
                KeyboardButton(text="Калькулятор маржи 💰"),
                KeyboardButton(text="Рекомендации ⚡"),
            ],
            [
                KeyboardButton(text="Премиум 🚀"),
            ],
        ],
        resize_keyboard=True,
    )


def _manager_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Анализ рынка 📊"),
                KeyboardButton(text="Подбор ниши 🧭"),
            ],
            [
                KeyboardButton(text="Калькулятор маржи 💰"),
                KeyboardButton(text="Рекомендации ⚡"),
            ],
            [
                KeyboardButton(text="Премиум 🚀"),
                KeyboardButton(text="Менеджер 📋"),
            ],
        ],
        resize_keyboard=True,
    )


def _owner_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Анализ рынка 📊"),
                KeyboardButton(text="Подбор ниши 🧭"),
            ],
            [
                KeyboardButton(text="Калькулятор маржи 💰"),
                KeyboardButton(text="Рекомендации ⚡"),
            ],
            [
                KeyboardButton(text="Премиум 🚀"),
                KeyboardButton(text="Админ 👑"),
            ],
        ],
        resize_keyboard=True,
    )


def get_main_keyboard(role: str) -> ReplyKeyboardMarkup:
    if role == ROLE_OWNER:
        return _owner_keyboard()
    if role == ROLE_MANAGER:
        return _manager_keyboard()
    return _user_keyboard()
