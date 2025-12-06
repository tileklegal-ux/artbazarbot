from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ---------- Клавиатура выбора языка ----------
language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Русский 🇷🇺")],
        [KeyboardButton(text="Кыргызча 🇰🇬")],
        [KeyboardButton(text="Қазақша 🇰🇿")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ---------- Меню пользователя ----------
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


# ---------- Меню менеджера ----------
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


# ---------- Меню владельца ----------
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
    if role == "owner":
        return _owner_keyboard()
    if role == "manager":
        return _manager_keyboard()
    return _user_keyboard()
