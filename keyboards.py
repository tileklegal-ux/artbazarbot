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


# ---------- USER меню (обычный пользователь) ----------
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


# ---------- MANAGER меню ----------
def _manager_keyboard() -> ReplyKeyboardMarkup:
    """
    Менеджер: тот же функционал анализа, но есть доступ в свою панель.
    """
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


# ---------- OWNER меню ----------
def _owner_keyboard() -> ReplyKeyboardMarkup:
    """
    Владелец: полный доступ + отдельная кнопка Админ 👑.
    """
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


# ---------- Публичная функция выбора клавиатуры по роли ----------
def get_main_keyboard(role: str) -> ReplyKeyboardMarkup:
    """
    role: "owner" / "manager" / всё остальное = user.
    """
    if role == "owner":
        return _owner_keyboard()
    if role == "manager":
        return _manager_keyboard()
    return _user_keyboard()
