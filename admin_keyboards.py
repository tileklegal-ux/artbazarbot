from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Панель владельца
owner_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выдать премиум 🎁")],
        [KeyboardButton(text="Список премиум 👥")],
        [KeyboardButton(text="Добавить менеджера ➕")],
        [KeyboardButton(text="Список менеджеров 📋")],
        [KeyboardButton(text="⬅️ В главное меню")],
    ],
    resize_keyboard=True,
)

# Панель менеджера
manager_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выдать премиум 🎁")],
        [KeyboardButton(text="Список премиум 👥")],
        [KeyboardButton(text="Поддержка 💬")],
        [KeyboardButton(text="⬅️ В главное меню")],
    ],
    resize_keyboard=True,
)

# Выбор тарифа премиума
premium_tariff_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="1 месяц"),
            KeyboardButton(text="6 месяцев"),
        ],
        [
            KeyboardButton(text="1 год"),
        ],
        [
            KeyboardButton(text="⬅️ В админку"),
        ],
    ],
    resize_keyboard=True,
)
